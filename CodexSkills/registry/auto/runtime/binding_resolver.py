"""Externally trusted adapter for the Mechanism BOUND reference resolver."""

from __future__ import annotations

import hashlib
import importlib
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.registry.auto.tools.validate_auto import TrustTuple

from .core import AutoRuntimeError, PROTOCOL


RESOLVER_INTERFACE_PATH = (
    "CodexSkills/governance/registry/resolver-interface.json"
)
REGISTERED_SNAPSHOT_PATH = (
    "CodexSkills/registry/_global/registry-snapshot.v1.json"
)
REGISTERED_SNAPSHOT_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:"
    "registry-snapshot:v1"
)
REGISTERED_MODE = "REGISTERED"
EXPECTED_RESOLVER_STATUS = (
    "DRAFT_NON_ACTIVE_PARITY_COMPLETE_MATERIALIZED"
)
EXPECTED_CONTROL_NEXT_PHASE = (
    "AUTO_BOUND_REFERENCE_RESOLVER_INTEGRATION"
)
EXPECTED_RUNTIME_PATHS = (
    "CodexSkills/governance/tools/build_bound_reference_resolver.py",
    "CodexSkills/governance/tools/resolve_skill_binding.py",
)
EXPECTED_SCHEMA_PATHS = {
    "urn:linzecolin:agentdatabase:skillops:schema:"
    "bound-reference-request:v1": (
        "CodexSkills/governance/registry/schemas/"
        "bound-reference-request.schema.json"
    ),
    "urn:linzecolin:agentdatabase:skillops:schema:"
    "registry-snapshot:v1": (
        "CodexSkills/governance/registry/schemas/"
        "registry-snapshot.schema.json"
    ),
    "urn:linzecolin:agentdatabase:skillops:schema:"
    "registry-source-catalog:v1": (
        "CodexSkills/governance/registry/schemas/"
        "registry-source-catalog.schema.json"
    ),
    "urn:linzecolin:agentdatabase:skillops:schema:"
    "registry-source-drift-reconciliation:v1": (
        "CodexSkills/governance/registry/schemas/"
        "registry-source-drift-reconciliation.schema.json"
    ),
}
EXPECTED_CATALOG_PATHS = {
    "AGENTS": "CodexSkills/registry/agents/_catalog/catalog.v1.json",
    "CLAUDE": "CodexSkills/registry/claude/_catalog/catalog.v1.json",
    "CODEX": "CodexSkills/registry/codex/_catalog/catalog.v1.json",
    "CODEX_SYSTEM": (
        "CodexSkills/registry/codex-system/_catalog/catalog.v1.json"
    ),
}
GIT_OBJECT_RE = re.compile(
    r"^(?:(sha1):([0-9a-f]{40})|(sha256):([0-9a-f]{64}))$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_INTERFACE_BYTES = 1024 * 1024
_PROOF_SEAL = object()


@dataclass(frozen=True)
class RegistrySnapshotTrustTuple:
    """Registry trust supplied outside the repository under verification."""

    verified_git_object_id: str
    canonical_snapshot_digest: str
    canonical_snapshot_path: str
    canonical_snapshot_schema_id: str
    mode: str


@dataclass(frozen=True)
class VerifiedBoundReferenceResolver:
    """Read-only proof returned only after full immutable Registry closure."""

    snapshot_trust: RegistrySnapshotTrustTuple
    resolver_interface_raw_sha256: str
    registry_snapshot_digest: str
    source_skill_count: int
    binding_eligible_version_count: int
    all_current_versions_unknown_verified: bool
    _module: Any = field(repr=False, compare=False)
    _context: Any = field(repr=False, compare=False)
    _seal: Any = field(repr=False, compare=False)

    def resolve(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        """Resolve through the verified Mechanism module and immutable context."""

        if self._module is None or self._context is None:
            raise AutoRuntimeError(
                "BOUND_REFERENCE_RESOLVER_PROOF_NOT_EXECUTABLE"
            )
        try:
            return self._module.resolve_binding(self._context, request)
        except self._module.ContractError as exc:
            reason = str(exc).split(":", 1)[0]
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", reason):
                reason = "CONTRACT_ERROR"
            raise AutoRuntimeError(
                "BOUND_REFERENCE_RESOLVER_FAILED:" + reason
            ) from exc


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
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_GIT_UNAVAILABLE"
        ) from exc
    if result.returncode != 0:
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_GIT_READ_FAILED"
        )
    return result.stdout


def _split_git_object(repo_root: Path, value: str) -> tuple[str, str]:
    match = GIT_OBJECT_RE.fullmatch(value)
    if match is None:
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_GIT_OBJECT_INVALID"
        )
    algorithm = match.group(1) or match.group(3)
    object_id = match.group(2) or match.group(4)
    observed = _run_git(
        repo_root,
        "rev-parse",
        "--show-object-format",
    ).decode("ascii", errors="strict").strip()
    if observed != algorithm:
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_GIT_ALGORITHM_MISMATCH"
        )
    _run_git(repo_root, "cat-file", "-e", f"{object_id}^{{commit}}")
    return algorithm, object_id


def _git_blob(repo_root: Path, object_id: str, relative_path: str) -> bytes:
    if (
        not isinstance(relative_path, str)
        or not relative_path
        or relative_path.startswith("/")
        or relative_path.endswith("/")
        or "\\" in relative_path
        or any(
            part in {"", ".", ".."}
            for part in relative_path.split("/")
        )
    ):
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_PATH_INVALID"
        )
    return _run_git(repo_root, "show", f"{object_id}:{relative_path}")


def _mapping(raw: bytes, code: str) -> Mapping[str, Any]:
    if not raw or len(raw) > MAX_INTERFACE_BYTES:
        raise AutoRuntimeError(code + "_BYTES_INVALID")
    try:
        value = parse_json_bytes(raw)
    except Exception as exc:
        raise AutoRuntimeError(code + "_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise AutoRuntimeError(code + "_ROOT_INVALID")
    return value


def _load_resolver_module(repo_root: Path):
    tools_path = (
        repo_root / "CodexSkills" / "governance" / "tools"
    ).resolve(strict=True)
    expected = {
        "canonical_json": (tools_path / "canonical_json.py").resolve(
            strict=True
        ),
        "resolve_skill_binding": (
            tools_path / "resolve_skill_binding.py"
        ).resolve(strict=True),
        "validate_mechanism": (
            tools_path / "validate_mechanism.py"
        ).resolve(strict=True),
    }
    for name, expected_path in expected.items():
        existing = sys.modules.get(name)
        if existing is None:
            continue
        observed = Path(
            str(getattr(existing, "__file__", ""))
        ).resolve()
        if observed != expected_path:
            raise AutoRuntimeError(
                "BOUND_REFERENCE_RESOLVER_MODULE_IDENTITY_CONFLICT"
            )
        del sys.modules[name]
    sys.path.insert(0, str(tools_path))
    try:
        module = importlib.import_module("resolve_skill_binding")
    except Exception as exc:
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_MODULE_IMPORT_FAILED"
        ) from exc
    finally:
        if sys.path and sys.path[0] == str(tools_path):
            sys.path.pop(0)
    observed = Path(str(getattr(module, "__file__", ""))).resolve()
    if observed != expected["resolve_skill_binding"]:
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_MODULE_IDENTITY_CONFLICT"
        )
    for name, expected_path in expected.items():
        loaded = sys.modules.get(name)
        if (
            loaded is None
            or Path(str(getattr(loaded, "__file__", ""))).resolve()
            != expected_path
        ):
            raise AutoRuntimeError(
                "BOUND_REFERENCE_RESOLVER_MODULE_IDENTITY_CONFLICT"
            )
    return module


def _verified_interface(
    repo_root: Path,
    object_id: str,
    candidate_trust: TrustTuple,
    control_interface: Mapping[str, Any],
    snapshot_trust: RegistrySnapshotTrustTuple,
) -> tuple[Mapping[str, Any], str]:
    resolver_contract = control_interface.get(
        "bound_reference_resolver_contract"
    )
    if not isinstance(resolver_contract, dict):
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_CONTROL_CONTRACT_INVALID"
        )
    expected_raw_digest = resolver_contract.get("artifact_digest")
    if not isinstance(expected_raw_digest, str) or not SHA256_RE.fullmatch(
        expected_raw_digest
    ):
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_CONTROL_DIGEST_INVALID"
        )
    raw = _git_blob(repo_root, object_id, RESOLVER_INTERFACE_PATH)
    if hashlib.sha256(raw).hexdigest() != expected_raw_digest:
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_INTERFACE_RAW_DIGEST_MISMATCH"
        )
    interface = _mapping(raw, "BOUND_REFERENCE_RESOLVER_INTERFACE")
    if (
        interface.get("artifact_digest")
        != canonical_digest(interface, "/artifact_digest")
        or interface.get("status") != EXPECTED_RESOLVER_STATUS
        or interface.get("protocol_revision") != PROTOCOL
        or interface.get("activation_forbidden") is not True
        or interface.get("candidate_git_object_id")
        != candidate_trust.verified_git_object_id
        or interface.get("bundle_digest")
        != candidate_trust.expected_bundle_digest
        or interface.get("candidate_manifest_path")
        != candidate_trust.canonical_manifest_path
        or interface.get("candidate_trust_mode")
        != candidate_trust.mode
        or interface.get("next_phase")
        != EXPECTED_CONTROL_NEXT_PHASE
        or interface.get("auto_integration_complete") is not False
        or interface.get("production_trust_permitted") is not False
        or interface.get("canonical_publication_permitted") is not False
        or interface.get("catalog_count") != 4
        or interface.get("schema_entry_count") != 4
        or interface.get("current_materialization_structurally_promoted")
        is not True
        or interface.get("exact_byte_promotion_complete") is not True
        or interface.get("source_mirror_parity_satisfied") is not True
        or interface.get("source_content_sync_required") is not False
    ):
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_INTERFACE_CONTRACT_MISMATCH"
        )
    registered = interface.get(
        "registered_snapshot_external_trust_contract"
    )
    snapshot = interface.get("registry_snapshot")
    resolver = interface.get("resolver_contract")
    if (
        not isinstance(registered, dict)
        or registered.get("canonical_snapshot_path")
        != snapshot_trust.canonical_snapshot_path
        or registered.get("canonical_snapshot_schema_id")
        != snapshot_trust.canonical_snapshot_schema_id
        or registered.get("mode") != snapshot_trust.mode
        or registered.get("registry_snapshot_digest")
        != snapshot_trust.canonical_snapshot_digest
        or registered.get("verified_git_object_id_source")
        != "REPO_EXTERNAL_MECHANISM_SUCCESSOR_COMMIT"
        or not isinstance(snapshot, dict)
        or snapshot.get("status") != REGISTERED_MODE
        or snapshot.get("proposed_final_relative_path")
        != snapshot_trust.canonical_snapshot_path
        or snapshot.get("schema_id")
        != snapshot_trust.canonical_snapshot_schema_id
        or snapshot.get("registry_snapshot_digest")
        != snapshot_trust.canonical_snapshot_digest
        or snapshot.get("current_source_skill_count") != 88
        or snapshot.get("current_identity_count") != 88
        or snapshot.get("current_instance_count") != 88
        or snapshot.get("current_version_count") != 88
        or snapshot.get("binding_eligible_version_count") != 0
        or snapshot.get("tracked_symlink_alias_count") != 20
        or not isinstance(resolver, dict)
        or resolver.get("current_snapshot_can_emit_bound") is not False
        or resolver.get("fail_closed_unknown_reason_code")
        != "MAPPING_NOT_PROVABLE"
        or resolver.get("full_seven_field_skill_ref_required")
        is not True
    ):
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_SNAPSHOT_CONTRACT_MISMATCH"
        )

    catalog_entries = interface.get("final_catalog_entries")
    if (
        not isinstance(catalog_entries, list)
        or len(catalog_entries) != len(EXPECTED_CATALOG_PATHS)
        or any(
            not isinstance(entry, dict)
            or entry.get("status") != REGISTERED_MODE
            or not isinstance(entry.get("artifact_digest"), str)
            or not SHA256_RE.fullmatch(entry["artifact_digest"])
            for entry in catalog_entries
        )
    ):
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_CATALOG_SET_MISMATCH"
        )
    observed_catalogs = {
        entry.get("source_class"): entry.get("relative_path")
        for entry in catalog_entries
    }
    if (
        observed_catalogs != EXPECTED_CATALOG_PATHS
        or len(observed_catalogs) != len(catalog_entries)
    ):
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_CATALOG_SET_MISMATCH"
        )
    schema_entries = interface.get("schema_entries")
    if (
        not isinstance(schema_entries, list)
        or len(schema_entries) != len(EXPECTED_SCHEMA_PATHS)
        or any(
            not isinstance(entry, dict)
            or not isinstance(entry.get("schema_sha256"), str)
            or not SHA256_RE.fullmatch(entry["schema_sha256"])
            for entry in schema_entries
        )
    ):
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_SCHEMA_SET_MISMATCH"
        )
    observed_schemas = {
        entry.get("id"): entry.get("relative_path")
        for entry in schema_entries
    }
    if (
        observed_schemas != EXPECTED_SCHEMA_PATHS
        or len(observed_schemas) != len(schema_entries)
    ):
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_SCHEMA_SET_MISMATCH"
        )
    runtime_artifacts = interface.get("runtime_artifacts")
    if (
        not isinstance(runtime_artifacts, list)
        or len(runtime_artifacts) != len(EXPECTED_RUNTIME_PATHS)
        or tuple(
            entry.get("relative_path")
            for entry in runtime_artifacts
            if isinstance(entry, dict)
        )
        != EXPECTED_RUNTIME_PATHS
    ):
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_RUNTIME_SET_MISMATCH"
        )
    for entry in runtime_artifacts:
        digest = entry.get("artifact_digest")
        relative_path = entry.get("relative_path")
        if (
            not isinstance(digest, str)
            or not SHA256_RE.fullmatch(digest)
            or not isinstance(relative_path, str)
        ):
            raise AutoRuntimeError(
                "BOUND_REFERENCE_RESOLVER_RUNTIME_ENTRY_INVALID"
            )
        pinned = _git_blob(repo_root, object_id, relative_path)
        if hashlib.sha256(pinned).hexdigest() != digest:
            raise AutoRuntimeError(
                "BOUND_REFERENCE_RESOLVER_RUNTIME_DIGEST_MISMATCH"
            )
        try:
            local = repo_root.joinpath(
                *relative_path.split("/")
            ).read_bytes()
        except OSError as exc:
            raise AutoRuntimeError(
                "BOUND_REFERENCE_RESOLVER_RUNTIME_READ_FAILED"
            ) from exc
        if local != pinned:
            raise AutoRuntimeError(
                "BOUND_REFERENCE_RESOLVER_RUNTIME_LOCAL_DRIFT"
            )
    return interface, expected_raw_digest


def _request_for_entry(
    module,
    entry: Mapping[str, Any],
    *,
    bundle_digest: str,
    source_class: str,
) -> Mapping[str, Any]:
    invocation = {
        "evidence_type": "CONTROLLED_INVOCATION_EXACT_VERSION",
        "invocation_envelope_digest": "0" * 64,
        "invocation_uid": "inv_" + "0" * 26,
        "observed_at": "2026-07-26T00:00:00.000000Z",
        "surface_class": "CODEX_CLI",
    }
    invocation["invocation_envelope_digest"] = module.canonical_digest(
        invocation,
        "/invocation_envelope_digest",
    )
    request = {
        "bundle_digest": bundle_digest,
        "content_digest": entry["material"]["content_digest"],
        "controlled_invocation": invocation,
        "envelope_digest": "0" * 64,
        "protocol_revision": PROTOCOL,
        "schema_version": module.REQUEST_ID,
        "source_class": source_class,
        "source_relative_path": entry["source_relative_path"],
        "tree_digest": entry["material"]["tree_digest"],
    }
    request["envelope_digest"] = module.canonical_digest(
        request,
        "/envelope_digest",
    )
    return request


def load_verified_bound_reference_resolver(
    repo_root: Path,
    candidate_trust: TrustTuple,
    control_trust: Any,
    control_interface: Mapping[str, Any],
    snapshot_trust: RegistrySnapshotTrustTuple,
) -> VerifiedBoundReferenceResolver:
    """Validate control, resolver, schemas, catalogs, and snapshot from Git."""

    root = repo_root.resolve(strict=True)
    if (
        snapshot_trust.verified_git_object_id
        != control_trust.verified_git_object_id
        or snapshot_trust.canonical_snapshot_path
        != REGISTERED_SNAPSHOT_PATH
        or snapshot_trust.canonical_snapshot_schema_id
        != REGISTERED_SNAPSHOT_SCHEMA_ID
        or snapshot_trust.mode != REGISTERED_MODE
        or not SHA256_RE.fullmatch(
            snapshot_trust.canonical_snapshot_digest
        )
    ):
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_EXTERNAL_TUPLE_MISMATCH"
        )
    _algorithm, object_id = _split_git_object(
        root,
        snapshot_trust.verified_git_object_id,
    )
    interface, interface_raw_digest = _verified_interface(
        root,
        object_id,
        candidate_trust,
        control_interface,
        snapshot_trust,
    )
    module = _load_resolver_module(root)
    try:
        context = module.load_trusted_registry(
            root,
            module.TrustTuple(
                candidate_trust.verified_git_object_id,
                candidate_trust.expected_bundle_digest,
                candidate_trust.canonical_manifest_path,
                candidate_trust.mode,
            ),
            module.RegistrySnapshotTrustTuple(
                snapshot_trust.verified_git_object_id,
                snapshot_trust.canonical_snapshot_digest,
                snapshot_trust.canonical_snapshot_path,
                snapshot_trust.canonical_snapshot_schema_id,
                snapshot_trust.mode,
            ),
        )
    except module.ContractError as exc:
        reason = str(exc).split(":", 1)[0]
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", reason):
            reason = "CONTRACT_ERROR"
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_TRUST_FAILED:" + reason
        ) from exc
    if (
        len(context.assignments) != 88
        or len(context.identities) != 88
        or len(context.instances) != 88
        or len(context.versions) != 88
        or len(context.catalogs) != 4
        or len(context.eligible_version_uids) != 0
        or context.snapshot.get("registry_snapshot_digest")
        != snapshot_trust.canonical_snapshot_digest
    ):
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_CONTEXT_CLOSURE_MISMATCH"
        )
    observed = 0
    for source_class in module.SOURCE_CLASSES:
        for entry in context.catalogs[source_class]["entries"]:
            request = _request_for_entry(
                module,
                entry,
                bundle_digest=context.snapshot["bundle_digest"],
                source_class=source_class,
            )
            result = module.resolve_binding(context, request)
            if result != {
                "binding_state": "UNKNOWN",
                "unknown_reason_code": "MAPPING_NOT_PROVABLE",
            }:
                raise AutoRuntimeError(
                    "BOUND_REFERENCE_RESOLVER_UNEXPECTED_BOUND"
                )
            observed += 1
    if observed != 88:
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_UNKNOWN_PROJECTION_COUNT_MISMATCH"
        )
    return VerifiedBoundReferenceResolver(
        snapshot_trust=snapshot_trust,
        resolver_interface_raw_sha256=interface_raw_digest,
        registry_snapshot_digest=(
            snapshot_trust.canonical_snapshot_digest
        ),
        source_skill_count=observed,
        binding_eligible_version_count=0,
        all_current_versions_unknown_verified=True,
        _module=module,
        _context=context,
        _seal=_PROOF_SEAL,
    )


def proof_is_sealed(value: object) -> bool:
    """Return true only for a proof constructed by this module's loader."""

    return (
        isinstance(value, VerifiedBoundReferenceResolver)
        and value._seal is _PROOF_SEAL
    )
