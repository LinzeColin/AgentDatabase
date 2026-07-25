#!/usr/bin/env python3
"""Resolve an observed invocation to one exact registered SkillVersion.

The resolver has two independent, repo-external trust roots:

* the active/candidate schema bundle tuple; and
* an immutable Registry snapshot tuple.

Repository self-reports, the compatibility index, a source/path name match, or
caller booleans never establish BOUND.  An observed invocation that cannot
close the exact identity -> instance -> version chain projects to UNKNOWN.
Malformed or untrusted inputs fail closed with ``ContractError``.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from jsonschema import Draft202012Validator

from canonical_json import (
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
)
from validate_mechanism import (
    ContractBundle,
    ContractError,
    PROTOCOL,
    TrustTuple,
    build_registry,
    load_trusted_bundle,
    scan_public_value,
    validate_instance,
)


SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
CATALOG_ID = SCHEMA_PREFIX + "registry-source-catalog:v1"
SNAPSHOT_ID = SCHEMA_PREFIX + "registry-snapshot:v1"
REQUEST_ID = SCHEMA_PREFIX + "bound-reference-request:v1"
BINDING_ID = SCHEMA_PREFIX + "skill-binding:v1"
IDENTITY_ID = SCHEMA_PREFIX + "skill-identity:v1"
INSTANCE_ID = SCHEMA_PREFIX + "skill-instance:v1"
VERSION_ID = SCHEMA_PREFIX + "skill-version:v1"

CATALOG_SCHEMA_PATH = (
    "CodexSkills/governance/registry/schemas/"
    "registry-source-catalog.schema.json"
)
SNAPSHOT_SCHEMA_PATH = (
    "CodexSkills/governance/registry/schemas/"
    "registry-snapshot.schema.json"
)
REQUEST_SCHEMA_PATH = (
    "CodexSkills/governance/registry/schemas/"
    "bound-reference-request.schema.json"
)
DRAFT_SNAPSHOT_PATH = (
    "CodexSkills/governance/registry/materialized/_global/"
    "registry-snapshot.v1.json"
)
REGISTERED_SNAPSHOT_PATH = (
    "CodexSkills/registry/_global/registry-snapshot.v1.json"
)

SOURCE_CLASSES = ("AGENTS", "CLAUDE", "CODEX", "CODEX_SYSTEM")
SOURCE_NAMES = {
    "AGENTS": "agents",
    "CLAUDE": "claude",
    "CODEX": "codex",
    "CODEX_SYSTEM": "codex-system",
}
ELIGIBLE_LIFECYCLE_STATES = {
    "REGISTERED",
    "EVALUATING",
    "CHALLENGER",
    "CHAMPION",
    "DEPRECATED",
}
ELIGIBLE_TRUST_TIERS = {"LOCAL_TRUSTED", "PINNED_UPSTREAM"}
GIT_OBJECT_RE = re.compile(
    r"^(?P<algorithm>sha1|sha256):"
    r"(?P<object>[0-9a-f]{40}|[0-9a-f]{64})$"
)


@dataclass(frozen=True)
class RegistrySnapshotTrustTuple:
    """Trust asserted outside the repository being verified."""

    verified_git_object_id: str
    canonical_snapshot_digest: str
    canonical_snapshot_path: str
    canonical_snapshot_schema_id: str
    mode: str


@dataclass(frozen=True)
class ResolverContext:
    bundle: ContractBundle
    schemas: Mapping[str, Any]
    schema_registry: Any
    format_checker: Any
    snapshot: Mapping[str, Any]
    catalogs: Mapping[str, Mapping[str, Any]]
    identities: Mapping[str, Mapping[str, Any]]
    instances: Mapping[str, Mapping[str, Any]]
    versions: Mapping[str, Mapping[str, Any]]
    assignments: Mapping[Tuple[str, str], str]
    eligible_version_uids: frozenset[str]
    trust_mode: str


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _object_digest(value: Any) -> str:
    return _sha(canonicalize_object(value))


def _tagged_object(value: str) -> Tuple[str, str]:
    match = GIT_OBJECT_RE.fullmatch(value)
    if match is None:
        raise ContractError("REGISTRY_TRUST_GIT_OBJECT_ID_INVALID")
    algorithm = match.group("algorithm")
    object_id = match.group("object")
    if (
        (algorithm == "sha1" and len(object_id) != 40)
        or (algorithm == "sha256" and len(object_id) != 64)
    ):
        raise ContractError("REGISTRY_TRUST_GIT_OBJECT_ID_INVALID")
    return algorithm, object_id


def _git(
    repo_root: Path,
    args: Sequence[str],
    *,
    binary: bool = False,
) -> Any:
    process = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=not binary,
    )
    if process.returncode != 0:
        stderr = (
            process.stderr.decode("utf-8", "replace")
            if binary
            else process.stderr
        )
        raise ContractError(
            "REGISTRY_TRUST_GIT_READ_FAILED:"
            + " ".join(args)
            + ":"
            + stderr.strip()
        )
    return process.stdout


def _git_blob(repo_root: Path, object_id: str, relative_path: str) -> bytes:
    if (
        not relative_path
        or relative_path.startswith("/")
        or relative_path.endswith("/")
        or "\\" in relative_path
        or any(
            part in {"", ".", ".."}
            for part in relative_path.split("/")
        )
    ):
        raise ContractError("REGISTRY_TRUST_PATH_INVALID")
    return _git(
        repo_root,
        ["show", f"{object_id}:{relative_path}"],
        binary=True,
    )


def _expected_snapshot_path(mode: str) -> str:
    if mode == "DRAFT_NON_ACTIVE":
        return DRAFT_SNAPSHOT_PATH
    if mode == "REGISTERED":
        return REGISTERED_SNAPSHOT_PATH
    raise ContractError("REGISTRY_TRUST_MODE_INVALID")


def _expected_catalog_path(source_class: str, mode: str) -> str:
    source = SOURCE_NAMES[source_class]
    if mode == "DRAFT_NON_ACTIVE":
        return (
            "CodexSkills/governance/registry/materialized/sources/"
            + source
            + "/catalog.v1.json"
        )
    if mode == "REGISTERED":
        return (
            "CodexSkills/registry/"
            + source
            + "/_catalog/catalog.v1.json"
        )
    raise ContractError("REGISTRY_TRUST_MODE_INVALID")


def _schema_errors(
    instance: Any,
    schema: Any,
    registry: Any,
    checker: Any,
) -> List[str]:
    errors = list(
        Draft202012Validator(
            schema,
            registry=registry,
            format_checker=checker,
        ).iter_errors(instance)
    )
    return [
        f"{'/'.join(str(item) for item in error.absolute_path)}:"
        f"{error.message}"
        for error in sorted(
            errors,
            key=lambda item: tuple(
                str(part) for part in item.absolute_path
            ),
        )
    ]


def _validate_schema_instance(
    *,
    instance: Any,
    schema_id: str,
    schemas: Mapping[str, Any],
    registry: Any,
    checker: Any,
    code: str,
) -> None:
    errors = _schema_errors(
        instance,
        schemas[schema_id],
        registry,
        checker,
    )
    if errors:
        raise ContractError(code + ":" + " | ".join(errors))


def _unique_records(
    rows: Any,
    uid_field: str,
    digest_field: str,
    code: str,
) -> Dict[str, Mapping[str, Any]]:
    if not isinstance(rows, list):
        raise ContractError(code + "_ROWS_INVALID")
    result: Dict[str, Mapping[str, Any]] = {}
    observed_order: List[str] = []
    for row in rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("record"), dict)
        ):
            raise ContractError(code + "_ROW_INVALID")
        record = row["record"]
        uid = record.get(uid_field)
        if not isinstance(uid, str) or uid in result:
            raise ContractError(code + "_UID_DUPLICATE_OR_INVALID")
        if _object_digest(record) != row.get(digest_field):
            raise ContractError(code + "_DIGEST_MISMATCH")
        result[uid] = record
        observed_order.append(uid)
    if observed_order != sorted(observed_order):
        raise ContractError(code + "_ORDER_INVALID")
    return result


def _permissions_are_known(permissions: Any) -> bool:
    return isinstance(permissions, dict) and all(
        value != "UNKNOWN" for value in permissions.values()
    )


def _version_is_eligible(
    identity: Mapping[str, Any],
    instance: Mapping[str, Any],
    version: Mapping[str, Any],
    metadata_state: str,
) -> bool:
    provenance = instance.get("provenance")
    return bool(
        metadata_state == "VALID"
        and identity.get("lifecycle_status")
        in ELIGIBLE_LIFECYCLE_STATES
        and instance.get("lifecycle_status")
        in ELIGIBLE_LIFECYCLE_STATES
        and version.get("lifecycle_status")
        in ELIGIBLE_LIFECYCLE_STATES
        and isinstance(provenance, dict)
        and provenance.get("license_state") == "KNOWN_ALLOWED"
        and provenance.get("trust_tier") in ELIGIBLE_TRUST_TIERS
        and version.get("trust_tier") in ELIGIBLE_TRUST_TIERS
        and _permissions_are_known(instance.get("permissions"))
        and _permissions_are_known(version.get("permissions"))
    )


def validate_registry_documents(
    *,
    bundle: ContractBundle,
    schemas: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    catalogs: Mapping[str, Mapping[str, Any]],
    expected_bundle_digest: str,
    expected_snapshot_digest: str,
    trust_mode: str,
) -> ResolverContext:
    """Validate a complete in-memory snapshot after external bytes are pinned."""

    if set(schemas) != {CATALOG_ID, SNAPSHOT_ID, REQUEST_ID}:
        raise ContractError("REGISTRY_SCHEMA_SET_MISMATCH")
    all_schemas = {**bundle.schemas, **schemas}
    registry, checker = build_registry(all_schemas)
    _validate_schema_instance(
        instance=snapshot,
        schema_id=SNAPSHOT_ID,
        schemas=all_schemas,
        registry=registry,
        checker=checker,
        code="REGISTRY_SNAPSHOT_SCHEMA_INVALID",
    )
    if snapshot.get("registry_snapshot_digest") != expected_snapshot_digest:
        raise ContractError("REGISTRY_SNAPSHOT_EXTERNAL_DIGEST_MISMATCH")
    if (
        canonical_digest(snapshot, "/registry_snapshot_digest")
        != expected_snapshot_digest
    ):
        raise ContractError("REGISTRY_SNAPSHOT_SELF_DIGEST_MISMATCH")
    if snapshot.get("protocol_revision") != PROTOCOL:
        raise ContractError("REGISTRY_SNAPSHOT_PROTOCOL_MISMATCH")
    if snapshot.get("bundle_digest") != expected_bundle_digest:
        raise ContractError("REGISTRY_SNAPSHOT_BUNDLE_CONTEXT_MISMATCH")
    policy_id = snapshot.get("source_material_policy_id")
    policy = bundle.policies.get(policy_id)
    if (
        not isinstance(policy, dict)
        or _object_digest(policy)
        != snapshot.get("source_material_policy_digest")
    ):
        raise ContractError("REGISTRY_SNAPSHOT_SOURCE_POLICY_MISMATCH")
    if trust_mode == "DRAFT_NON_ACTIVE":
        expected_status = "DRAFT_NON_ACTIVE"
    elif trust_mode == "REGISTERED":
        expected_status = "REGISTERED"
    else:
        raise ContractError("REGISTRY_TRUST_MODE_INVALID")
    if snapshot.get("status") != expected_status:
        raise ContractError("REGISTRY_SNAPSHOT_MODE_STATUS_MISMATCH")
    scan_public_value(snapshot, bundle.policies)

    identities = _unique_records(
        snapshot.get("identities"),
        "skill_identity_uid",
        "artifact_digest",
        "REGISTRY_IDENTITY",
    )
    instances = _unique_records(
        snapshot.get("instances"),
        "skill_instance_uid",
        "artifact_digest",
        "REGISTRY_INSTANCE",
    )
    versions = _unique_records(
        snapshot.get("versions"),
        "skill_version_uid",
        "version_record_digest",
        "REGISTRY_VERSION",
    )
    expected_bundle_digest = snapshot["bundle_digest"]
    for record in identities.values():
        validate_instance(
            bundle,
            record,
            IDENTITY_ID,
            expected_bundle_digest=expected_bundle_digest,
            public=True,
        )
    for record in instances.values():
        validate_instance(
            bundle,
            record,
            INSTANCE_ID,
            expected_bundle_digest=expected_bundle_digest,
            public=True,
        )
    for record in versions.values():
        validate_instance(
            bundle,
            record,
            VERSION_ID,
            expected_bundle_digest=expected_bundle_digest,
            public=True,
        )

    for identity_uid, identity in identities.items():
        for instance_uid in identity["instance_uids"]:
            instance = instances.get(instance_uid)
            if (
                instance is None
                or instance["skill_identity_uid"] != identity_uid
            ):
                raise ContractError("REGISTRY_IDENTITY_INSTANCE_DANGLING")
    for instance_uid, instance in instances.items():
        identity = identities.get(instance["skill_identity_uid"])
        if (
            identity is None
            or instance_uid not in identity["instance_uids"]
        ):
            raise ContractError("REGISTRY_INSTANCE_IDENTITY_DANGLING")
        for version_uid in instance["version_uids"]:
            version = versions.get(version_uid)
            if (
                version is None
                or version["skill_instance_uid"] != instance_uid
            ):
                raise ContractError("REGISTRY_INSTANCE_VERSION_DANGLING")
    for version_uid, version in versions.items():
        instance = instances.get(version["skill_instance_uid"])
        if instance is None or version_uid not in instance["version_uids"]:
            raise ContractError("REGISTRY_VERSION_INSTANCE_DANGLING")

    assignments: Dict[Tuple[str, str], str] = {}
    assignment_order: List[str] = []
    for assignment in snapshot["identity_assignments"]:
        key = (
            assignment["source_class"],
            assignment["source_relative_path"],
        )
        if key in assignments:
            raise ContractError("REGISTRY_ASSIGNMENT_DUPLICATE")
        identity_uid = assignment["skill_identity_uid"]
        if identity_uid not in identities:
            raise ContractError("REGISTRY_ASSIGNMENT_IDENTITY_DANGLING")
        assignments[key] = identity_uid
        assignment_order.append(assignment["source_relative_path"])
    if assignment_order != sorted(
        assignment_order, key=lambda value: value.encode("utf-8")
    ):
        raise ContractError("REGISTRY_ASSIGNMENT_ORDER_INVALID")

    if set(catalogs) != set(SOURCE_CLASSES):
        raise ContractError("REGISTRY_CATALOG_SOURCE_SET_MISMATCH")
    catalog_refs = snapshot["source_catalogs"]
    if [
        row["source_class"] for row in catalog_refs
    ] != list(SOURCE_CLASSES):
        raise ContractError("REGISTRY_CATALOG_REF_ORDER_INVALID")
    catalog_entries: Dict[Tuple[str, str], Mapping[str, Any]] = {}
    for catalog_ref in catalog_refs:
        source_class = catalog_ref["source_class"]
        if (
            catalog_ref["draft_relative_path"]
            != _expected_catalog_path(
                source_class,
                "DRAFT_NON_ACTIVE",
            )
            or catalog_ref["proposed_final_relative_path"]
            != _expected_catalog_path(source_class, "REGISTERED")
        ):
            raise ContractError("REGISTRY_CATALOG_REF_PATH_MISMATCH")
        catalog = catalogs[source_class]
        _validate_schema_instance(
            instance=catalog,
            schema_id=CATALOG_ID,
            schemas=all_schemas,
            registry=registry,
            checker=checker,
            code="REGISTRY_CATALOG_SCHEMA_INVALID",
        )
        if catalog.get("status") != expected_status:
            raise ContractError("REGISTRY_CATALOG_MODE_STATUS_MISMATCH")
        if (
            catalog.get("artifact_digest")
            != catalog_ref["artifact_digest"]
            or canonical_digest(catalog, "/artifact_digest")
            != catalog_ref["artifact_digest"]
        ):
            raise ContractError("REGISTRY_CATALOG_DIGEST_MISMATCH")
        if (
            catalog.get("bundle_digest") != expected_bundle_digest
            or catalog.get("source_class") != source_class
            or catalog.get("source_root_path")
            != (
                "CodexSkills/registry/"
                + SOURCE_NAMES[source_class]
            )
            or catalog.get("entry_count") != len(catalog["entries"])
            or catalog_ref["entry_count"] != len(catalog["entries"])
            or catalog.get("source_material_git_object_id")
            != snapshot.get("source_material_git_object_id")
            or catalog.get("source_material_policy_id")
            != snapshot.get("source_material_policy_id")
            or catalog.get("source_material_policy_digest")
            != snapshot.get("source_material_policy_digest")
        ):
            raise ContractError("REGISTRY_CATALOG_CONTEXT_MISMATCH")
        scan_public_value(catalog, bundle.policies)
        observed_paths: List[str] = []
        for entry in catalog["entries"]:
            source_path = entry["source_relative_path"]
            if not source_path.startswith(
                SOURCE_NAMES[source_class] + "/"
            ):
                raise ContractError(
                    "REGISTRY_CATALOG_SOURCE_PATH_MISMATCH"
                )
            observed_paths.append(source_path)
            key = (source_class, source_path)
            if key in catalog_entries:
                raise ContractError("REGISTRY_CATALOG_ENTRY_DUPLICATE")
            identity_uid = entry["identity_ref"]["skill_identity_uid"]
            instance_uid = entry["instance_ref"]["skill_instance_uid"]
            version_uid = entry["version_ref"]["skill_version_uid"]
            identity = identities.get(identity_uid)
            instance = instances.get(instance_uid)
            version = versions.get(version_uid)
            if (
                identity is None
                or instance is None
                or version is None
                or assignments.get(key) != identity_uid
                or identity["canonical_name"]
                != entry["canonical_name"]
                or instance["skill_identity_uid"] != identity_uid
                or instance["source_class"] != source_class
                or instance["source_relative_path"] != source_path
                or version["skill_instance_uid"] != instance_uid
                or entry["identity_ref"]["artifact_digest"]
                != _object_digest(identity)
                or entry["instance_ref"]["artifact_digest"]
                != _object_digest(instance)
                or entry["version_ref"]["version_record_digest"]
                != _object_digest(version)
                or entry["material"]["content_digest"]
                != version["content_digest"]
                or entry["material"]["tree_digest"]
                != version["tree_digest"]
            ):
                raise ContractError("REGISTRY_CATALOG_RECORD_CLOSURE_INVALID")
            catalog_entries[key] = entry
        if observed_paths != sorted(
            observed_paths, key=lambda value: value.encode("utf-8")
        ):
            raise ContractError("REGISTRY_CATALOG_ENTRY_ORDER_INVALID")
    if set(catalog_entries) != set(assignments):
        raise ContractError("REGISTRY_ASSIGNMENT_CATALOG_SET_MISMATCH")

    expected_merge_candidates: List[Mapping[str, Any]] = []
    by_name: Dict[str, List[str]] = {}
    for identity_uid, identity in identities.items():
        by_name.setdefault(identity["canonical_name"], []).append(
            identity_uid
        )
    for name, uids in sorted(by_name.items()):
        if len(uids) > 1:
            expected_merge_candidates.append(
                {
                    "canonical_name": name,
                    "identity_uids": sorted(uids),
                    "reason_code": "OWNER_REVIEW_REQUIRED",
                }
            )
    if snapshot["identity_merge_candidates"] != expected_merge_candidates:
        raise ContractError("REGISTRY_MERGE_CANDIDATE_SET_MISMATCH")

    parity = snapshot["source_mirror_parity"]
    if parity["status"] == "COMPLETE":
        if (
            parity["binding_eligible"] is not True
            or parity["reason_codes"] != []
            or parity["tracked_symlink_alias_count"]
            != parity["expected_external_symlink_alias_count"]
        ):
            raise ContractError("REGISTRY_COMPLETE_PARITY_INVALID")
    elif (
        parity["binding_eligible"] is not False
        or not parity["reason_codes"]
    ):
        raise ContractError("REGISTRY_INCOMPLETE_PARITY_INVALID")

    eligible: set[str] = set()
    if (
        trust_mode == "REGISTERED"
        and parity["status"] == "COMPLETE"
        and parity["binding_eligible"] is True
    ):
        for key, entry in catalog_entries.items():
            identity_uid = assignments[key]
            identity = identities[identity_uid]
            instance_uid = entry["instance_ref"]["skill_instance_uid"]
            instance = instances[instance_uid]
            version_uid = entry["version_ref"]["skill_version_uid"]
            version = versions[version_uid]
            if _version_is_eligible(
                identity,
                instance,
                version,
                entry["material"]["metadata_state"],
            ):
                eligible.add(version_uid)

    counts = snapshot["counts"]
    expected_counts = {
        "binding_eligible_version_count": len(eligible),
        "identity_count": len(identities),
        "instance_count": len(instances),
        "metadata_invalid_count": sum(
            entry["material"]["metadata_state"] == "INVALID"
            for entry in catalog_entries.values()
        ),
        "quarantined_version_count": sum(
            record["lifecycle_status"] == "QUARANTINED"
            for record in versions.values()
        ),
        "source_catalog_count": len(catalogs),
        "source_skill_count": len(assignments),
        "tracked_symlink_alias_count": sum(
            entry["material"]["symlink_alias_count"]
            for entry in catalog_entries.values()
        ),
        "version_count": len(versions),
    }
    if counts != expected_counts:
        raise ContractError("REGISTRY_SNAPSHOT_COUNT_MISMATCH")

    return ResolverContext(
        bundle=bundle,
        schemas=schemas,
        schema_registry=registry,
        format_checker=checker,
        snapshot=snapshot,
        catalogs=catalogs,
        identities=identities,
        instances=instances,
        versions=versions,
        assignments=assignments,
        eligible_version_uids=frozenset(eligible),
        trust_mode=trust_mode,
    )


def load_trusted_registry(
    repo_root: Path,
    candidate_trust: TrustTuple,
    snapshot_trust: RegistrySnapshotTrustTuple,
) -> ResolverContext:
    """Load the candidate bundle and Registry only from external trust tuples."""

    bundle = load_trusted_bundle(repo_root, candidate_trust)
    algorithm, object_id = _tagged_object(
        snapshot_trust.verified_git_object_id
    )
    observed_algorithm = _git(
        repo_root,
        ["rev-parse", "--show-object-format"],
    ).strip()
    if observed_algorithm != algorithm:
        raise ContractError("REGISTRY_TRUST_GIT_ALGORITHM_MISMATCH")
    _git(repo_root, ["cat-file", "-e", f"{object_id}^{{commit}}"])
    if (
        snapshot_trust.canonical_snapshot_schema_id != SNAPSHOT_ID
        or snapshot_trust.canonical_snapshot_path
        != _expected_snapshot_path(snapshot_trust.mode)
    ):
        raise ContractError("REGISTRY_TRUST_TUPLE_CONTRACT_MISMATCH")
    schema_paths = {
        CATALOG_ID: CATALOG_SCHEMA_PATH,
        SNAPSHOT_ID: SNAPSHOT_SCHEMA_PATH,
        REQUEST_ID: REQUEST_SCHEMA_PATH,
    }
    schemas: Dict[str, Any] = {}
    for schema_id, path in schema_paths.items():
        document = parse_json_bytes(_git_blob(repo_root, object_id, path))
        if (
            not isinstance(document, dict)
            or document.get("$id") != schema_id
        ):
            raise ContractError("REGISTRY_TRUST_SCHEMA_ID_MISMATCH")
        schemas[schema_id] = document
    snapshot = parse_json_bytes(
        _git_blob(
            repo_root,
            object_id,
            snapshot_trust.canonical_snapshot_path,
        )
    )
    if not isinstance(snapshot, dict):
        raise ContractError("REGISTRY_TRUST_SNAPSHOT_ROOT_INVALID")
    catalogs: Dict[str, Mapping[str, Any]] = {}
    for source_class in SOURCE_CLASSES:
        catalog = parse_json_bytes(
            _git_blob(
                repo_root,
                object_id,
                _expected_catalog_path(
                    source_class,
                    snapshot_trust.mode,
                ),
            )
        )
        if not isinstance(catalog, dict):
            raise ContractError("REGISTRY_TRUST_CATALOG_ROOT_INVALID")
        catalogs[source_class] = catalog
    return validate_registry_documents(
        bundle=bundle,
        schemas=schemas,
        snapshot=snapshot,
        catalogs=catalogs,
        expected_bundle_digest=candidate_trust.expected_bundle_digest,
        expected_snapshot_digest=(
            snapshot_trust.canonical_snapshot_digest
        ),
        trust_mode=snapshot_trust.mode,
    )


def _unknown(context: ResolverContext) -> Mapping[str, Any]:
    result = {
        "binding_state": "UNKNOWN",
        "unknown_reason_code": "MAPPING_NOT_PROVABLE",
    }
    validate_instance(
        context.bundle,
        result,
        BINDING_ID,
        expected_bundle_digest=context.snapshot["bundle_digest"],
        public=True,
    )
    return result


def resolve_binding(
    context: ResolverContext,
    request: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Return BOUND only when all exact immutable references close."""

    _validate_schema_instance(
        instance=request,
        schema_id=REQUEST_ID,
        schemas={**context.bundle.schemas, **context.schemas},
        registry=context.schema_registry,
        checker=context.format_checker,
        code="BOUND_REFERENCE_REQUEST_SCHEMA_INVALID",
    )
    if (
        canonical_digest(request, "/envelope_digest")
        != request.get("envelope_digest")
    ):
        raise ContractError("BOUND_REFERENCE_REQUEST_DIGEST_MISMATCH")
    if (
        canonical_digest(
            request["controlled_invocation"],
            "/invocation_envelope_digest",
        )
        != request["controlled_invocation"][
            "invocation_envelope_digest"
        ]
    ):
        raise ContractError(
            "BOUND_REFERENCE_CONTROLLED_INVOCATION_DIGEST_MISMATCH"
        )
    if (
        request.get("protocol_revision") != PROTOCOL
        or request.get("bundle_digest")
        != context.snapshot.get("bundle_digest")
    ):
        raise ContractError("BOUND_REFERENCE_REQUEST_CONTEXT_MISMATCH")
    scan_public_value(request, context.bundle.policies)

    key = (
        request["source_class"],
        request["source_relative_path"],
    )
    identity_uid = context.assignments.get(key)
    catalog = context.catalogs.get(request["source_class"])
    if identity_uid is None or catalog is None:
        return _unknown(context)
    matches = [
        entry
        for entry in catalog["entries"]
        if entry["source_relative_path"]
        == request["source_relative_path"]
    ]
    if len(matches) != 1:
        return _unknown(context)
    entry = matches[0]
    instance_uid = entry["instance_ref"]["skill_instance_uid"]
    version_uid = entry["version_ref"]["skill_version_uid"]
    version = context.versions[version_uid]
    if (
        version_uid not in context.eligible_version_uids
        or request["content_digest"] != version["content_digest"]
        or request["tree_digest"] != version["tree_digest"]
    ):
        return _unknown(context)

    result = {
        "binding_state": "BOUND",
        "controlled_invocation": request["controlled_invocation"],
        "skill_ref": {
            "content_digest": version["content_digest"],
            "registry_snapshot_digest": context.snapshot[
                "registry_snapshot_digest"
            ],
            "skill_identity_uid": identity_uid,
            "skill_instance_uid": instance_uid,
            "skill_version_uid": version_uid,
            "tree_digest": version["tree_digest"],
            "version_record_digest": entry["version_ref"][
                "version_record_digest"
            ],
        },
    }
    validate_instance(
        context.bundle,
        result,
        BINDING_ID,
        expected_bundle_digest=context.snapshot["bundle_digest"],
        public=True,
    )
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--candidate-git-object-id", required=True)
    parser.add_argument("--candidate-bundle-digest", required=True)
    parser.add_argument("--candidate-manifest-path", required=True)
    parser.add_argument(
        "--candidate-mode",
        choices=("CANDIDATE", "ACTIVE"),
        required=True,
    )
    parser.add_argument("--snapshot-git-object-id", required=True)
    parser.add_argument("--snapshot-digest", required=True)
    parser.add_argument("--snapshot-path", required=True)
    parser.add_argument("--snapshot-schema-id", required=True)
    parser.add_argument(
        "--snapshot-mode",
        choices=("DRAFT_NON_ACTIVE", "REGISTERED"),
        required=True,
    )
    args = parser.parse_args(argv)
    try:
        repo_root = args.repo_root.resolve(strict=True)
        request = parse_json_bytes(sys.stdin.buffer.read())
        if not isinstance(request, dict):
            raise ContractError("BOUND_REFERENCE_REQUEST_ROOT_INVALID")
        context = load_trusted_registry(
            repo_root,
            TrustTuple(
                args.candidate_git_object_id,
                args.candidate_bundle_digest,
                args.candidate_manifest_path,
                args.candidate_mode,
            ),
            RegistrySnapshotTrustTuple(
                args.snapshot_git_object_id,
                args.snapshot_digest,
                args.snapshot_path,
                args.snapshot_schema_id,
                args.snapshot_mode,
            ),
        )
        output = resolve_binding(context, request)
        sys.stdout.buffer.write(canonicalize_object(output) + b"\n")
        return 0
    except (ContractError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
