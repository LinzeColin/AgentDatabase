"""Read-only capability and external-trust bootstrap for every run."""

from __future__ import annotations

import hashlib
import importlib.metadata
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from CodexSkills.auto.tools.validate_auto import (
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
    "CodexSkills/governance/tools/canonical_json.py",
    "CodexSkills/governance/tools/validate_mechanism.py",
    "CodexSkills/governance/vendor/json_canonicalization/PROVENANCE.json",
    "CodexSkills/governance/vendor/json_canonicalization/python3/src/org/webpki/json/Canonicalize.py",
    "CodexSkills/governance/vendor/json_canonicalization/python3/src/org/webpki/json/NumberToJson.py",
    "CodexSkills/governance/vendor/json_canonicalization/python3/src/org/webpki/json/LICENSE",
    "CodexSkills/governance/vendor/json_canonicalization/python3/src/org/webpki/json/LICENSE.PSF",
)


@dataclass(frozen=True)
class BootstrapContext:
    trust: TrustTuple
    contract: AutoContract
    capabilities: Mapping[str, str]


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


def _verify_local_mechanism_runtime(repo_root: Path, object_id: str) -> None:
    for relative_path in TRUSTED_MECHANISM_RUNTIME_PATHS:
        try:
            local = repo_root.joinpath(*relative_path.split("/")).read_bytes()
        except OSError as exc:
            raise AutoRuntimeError("BOOTSTRAP_TRUSTED_RUNTIME_READ_FAILED") from exc
        if local != _git_blob(repo_root, object_id, relative_path):
            raise AutoRuntimeError("BOOTSTRAP_TRUSTED_RUNTIME_LOCAL_DRIFT")


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


def bootstrap_runtime(repo_root: Path, trust: TrustTuple) -> BootstrapContext:
    """Validate all capabilities/trust before callers create runtime state."""

    root = repo_root.resolve()
    observed_root = _run_git(root, "rev-parse", "--show-toplevel").stdout.decode(
        "utf-8", errors="strict"
    ).strip()
    if Path(observed_root).resolve() != root:
        raise AutoRuntimeError("BOOTSTRAP_REPOSITORY_ROOT_MISMATCH")
    if trust.canonical_manifest_path != CANDIDATE_MANIFEST_PATH:
        raise AutoRuntimeError("BOOTSTRAP_MANIFEST_PATH_MISMATCH")
    object_id = trust.verified_git_object_id.split(":", 1)[-1]
    _verify_local_mechanism_runtime(root, object_id)
    capabilities = _capability_smoke(root)
    try:
        contract = load_trusted_auto_contract(root, trust)
    except ContractError as exc:
        raise AutoRuntimeError(f"BOOTSTRAP_TRUST_FAILED:{exc}") from exc

    version_exists = _git_path_exists(root, object_id, "CodexSkills/VERSION")
    if trust.mode == "CANDIDATE" and version_exists:
        raise AutoRuntimeError("BOOTSTRAP_CANDIDATE_ACTIVE_VERSION_FORBIDDEN")
    if trust.mode == "ACTIVE" and not version_exists:
        raise AutoRuntimeError("BOOTSTRAP_ACTIVE_VERSION_REQUIRED")
    return BootstrapContext(trust, contract, capabilities)
