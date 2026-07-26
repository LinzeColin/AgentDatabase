#!/usr/bin/env python3
"""Build/check non-active Mechanism M-064 Git-history disclosure evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from CodexSkills.governance.retention.git_history_disclosure import (  # noqa: E402
    DISCLOSURE_SCHEMA_ID,
    DISCLOSURE_SELF_POINTER,
    GitHistoryDisclosureError,
    PROTOCOL_REVISION,
    build_disclosure,
    render_disclosure_markdown,
    validate_disclosure,
    validate_disclosure_markdown,
    validate_disclosure_surface,
)
from CodexSkills.governance.tools import (  # noqa: E402
    build_git_active_tree_365d_policy as m063_builder,
)
from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_au040_semantic_acceptance import (  # noqa: E402
    load_au040_acceptance,
)
from CodexSkills.governance.tools.validate_mechanism import (  # noqa: E402
    ContractBundle,
    ContractError,
    build_registry,
    scan_public_value,
    validate_instance,
)


GOVERNANCE_DIR = REPO_ROOT / "CodexSkills" / "governance"
RETENTION_DIR = GOVERNANCE_DIR / "retention"
SCHEMA_DIR = RETENTION_DIR / "schemas"
COMPONENT_PATH = RETENTION_DIR / "git_history_disclosure.py"
DISCLOSURE_PATH = (
    RETENTION_DIR / "git-history-persistence-disclosure.json"
)
DISCLOSURE_MARKDOWN_PATH = (
    RETENTION_DIR / "GIT_HISTORY_PERSISTENCE_DISCLOSURE.md"
)
DISCLOSURE_SCHEMA_PATH = (
    SCHEMA_DIR / "git-history-persistence-disclosure.schema.json"
)
READINESS_PATH = (
    RETENTION_DIR / "git-history-persistence-readiness.json"
)
READINESS_SCHEMA_PATH = (
    SCHEMA_DIR / "git-history-persistence-readiness.schema.json"
)
VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

READINESS_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:git-history-persistence-readiness:v1"
)
NEXT_PHASE = "MECHANISM_READ_ONLY_MIGRATION_CUTOVER"

CANDIDATE_GIT_OBJECT = (
    "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5"
)
CANDIDATE_BUNDLE_DIGEST = (
    "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
)
CANDIDATE_MANIFEST_PATH = (
    "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
)
CANDIDATE_MANIFEST_RAW_SHA256 = (
    "66ad125629cab71739ff2bc266219f995f7a45998936ca720c6db678ee77e65a"
)

M063_GIT_OBJECT = (
    "sha1:039f3844b36961f1d8432b9c0d86d6cda408f430"
)
M063_READINESS_PATH = (
    "CodexSkills/governance/retention/"
    "git-active-tree-365d-readiness.json"
)
M063_READINESS_RAW_SHA256 = (
    "91592f339854fb205993e96a67698d7b6ce8fc54afd3b226f3090dfd49ab86f2"
)
M063_READINESS_SELF_DIGEST = (
    "0bb6c1fb335115785495805ed001d6747a311dd1cbee335547beccaf8501df88"
)
M063_COMPONENT_PATH = (
    "CodexSkills/governance/retention/git_active_tree_policy.py"
)
M063_COMPONENT_RAW_SHA256 = (
    "5789e1051c3060cfb1d221c710a51f47a631174708248a633e1e13c9becf8421"
)
M063_SCHEMA_CONTRACTS = (
    (
        "CodexSkills/governance/retention/schemas/"
        "git-active-tree-retention-observation.schema.json",
        "d19e6f5d3a241c2826372974429b74b6afd86d6f3a0b68f30d52e994cc914b69",
        "69858467989a55491ac8a8fe5654084fd94bc486a8d7c02ca732d2b62795af1a",
    ),
    (
        "CodexSkills/governance/retention/schemas/"
        "git-active-tree-prune-plan.schema.json",
        "94638455b8e2872fb612e73266d493683ce616e3a274a7a08ecc94c903335c73",
        "d1487922673949f63b4701c1f8988b5acec8a2a13011f231f85c56a874767b0c",
    ),
    (
        "CodexSkills/governance/retention/schemas/"
        "git-active-tree-365d-readiness.schema.json",
        "45cbe67d5093a41aaec3f726bd1976949b05b9244f32a9f8df6cc314221fe3d7",
        "17699af2a0967df8b7160cb1f3e4fd1e452a8e69eadce0dbe56cf9c1e03aa168",
    ),
)

DISCLOSURE_SURFACE_ROOTS = (
    "CodexSkills/governance",
    "CodexSkills/registry/auto",
    "OpenAIDatabase/data/run_logs",
)
CANONICAL_DISCLOSURE_PATH = (
    "CodexSkills/governance/retention/"
    "GIT_HISTORY_PERSISTENCE_DISCLOSURE.md"
)

REF = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:common-definitions:v1#/$defs/"
)


class GitHistoryDisclosureBuildError(ValueError):
    """M-064 material cannot be reproduced without weakening a gate."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _render(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _load_object(raw: bytes, code: str) -> Mapping[str, Any]:
    try:
        value = parse_json_bytes(raw)
    except Exception as exc:
        raise GitHistoryDisclosureBuildError(code) from exc
    if not isinstance(value, dict):
        raise GitHistoryDisclosureBuildError(code)
    return value


def _git_blob(tagged_object: str, relative_path: str) -> bytes:
    if tagged_object.count(":") != 1:
        raise GitHistoryDisclosureBuildError(
            "M064_GIT_OBJECT_INVALID"
        )
    algorithm, object_id = tagged_object.split(":", 1)
    if algorithm != "sha1" or len(object_id) != 40:
        raise GitHistoryDisclosureBuildError(
            "M064_GIT_OBJECT_INVALID"
        )
    try:
        process = subprocess.run(
            [
                "git",
                "-C",
                str(REPO_ROOT),
                "show",
                object_id + ":" + relative_path,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GitHistoryDisclosureBuildError(
            "M064_GIT_UNAVAILABLE"
        ) from exc
    if process.returncode != 0:
        raise GitHistoryDisclosureBuildError(
            "M064_GIT_BLOB_UNAVAILABLE:" + relative_path
        )
    return process.stdout


def _current(relative_path: str) -> bytes:
    path = REPO_ROOT.joinpath(*relative_path.split("/"))
    if not path.is_file() or path.is_symlink():
        raise GitHistoryDisclosureBuildError(
            "M064_CURRENT_FILE_INVALID:" + relative_path
        )
    return path.read_bytes()


def _validate_predecessor() -> Mapping[str, Any]:
    contracts = (
        (
            M063_READINESS_PATH,
            M063_READINESS_RAW_SHA256,
            None,
        ),
        (
            M063_COMPONENT_PATH,
            M063_COMPONENT_RAW_SHA256,
            None,
        ),
        *M063_SCHEMA_CONTRACTS,
    )
    for relative_path, raw_digest, schema_digest in contracts:
        historical = _git_blob(M063_GIT_OBJECT, relative_path)
        if _sha256(historical) != raw_digest:
            raise GitHistoryDisclosureBuildError(
                "M064_M063_HISTORICAL_RAW_DRIFT:" + relative_path
            )
        if _current(relative_path) != historical:
            raise GitHistoryDisclosureBuildError(
                "M064_M063_CURRENT_DRIFT:" + relative_path
            )
        if schema_digest is not None:
            if canonical_digest(
                _load_object(
                    historical,
                    "M064_M063_SCHEMA_INVALID:" + relative_path,
                )
            ) != schema_digest:
                raise GitHistoryDisclosureBuildError(
                    "M064_M063_SCHEMA_DIGEST_DRIFT:" + relative_path
                )
    readiness = _load_object(
        _git_blob(M063_GIT_OBJECT, M063_READINESS_PATH),
        "M064_M063_READINESS_INVALID",
    )
    if (
        readiness.get("status")
        != "DRAFT_NON_ACTIVE_GIT_ACTIVE_TREE_365D_READY"
        or readiness.get("artifact_digest")
        != M063_READINESS_SELF_DIGEST
        or readiness.get("artifact_digest")
        != canonical_digest(readiness, "/artifact_digest")
        or readiness.get("next_phase")
        != "MECHANISM_GIT_HISTORY_PERSISTENCE_DISCLOSURE"
        or readiness.get("task_contract", {}).get("completed_task_ids")
        != ["M-063"]
        or readiness.get("task_contract", {}).get("pending_task_ids")
        != ["M-064"]
        or readiness.get("real_execution_permitted") is not False
    ):
        raise GitHistoryDisclosureBuildError(
            "M064_M063_READINESS_CONTRACT_INVALID"
        )
    m063_builder._check()
    return readiness


def _ref(name: str) -> Mapping[str, str]:
    return {"$ref": REF + name}


def build_disclosure_schema(
    disclosure: Mapping[str, Any],
) -> Mapping[str, Any]:
    properties: Dict[str, Any] = {
        key: {"const": value}
        for key, value in disclosure.items()
        if key != "artifact_digest"
    }
    properties["artifact_digest"] = _ref("sha256")
    return {
        "$id": DISCLOSURE_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(disclosure),
        "title": "Mechanism M-064 Git-history persistence disclosure",
        "type": "object",
    }


def _extend_bundle(
    base: ContractBundle,
    additions: Mapping[str, Mapping[str, Any]],
    self_pointers: Mapping[str, str],
) -> ContractBundle:
    schemas = dict(base.schemas)
    pointers = dict(base.self_digest_pointers)
    for schema_id, schema in additions.items():
        if schema_id in schemas:
            raise GitHistoryDisclosureBuildError(
                "M064_SCHEMA_REBIND_FORBIDDEN:" + schema_id
            )
        schemas[schema_id] = schema
        pointers[schema_id] = self_pointers[schema_id]
    try:
        registry, format_checker = build_registry(schemas)
    except ContractError as exc:
        raise GitHistoryDisclosureBuildError(
            "M064_SCHEMA_CLOSURE_INVALID:" + str(exc)
        ) from exc
    return ContractBundle(
        schemas=schemas,
        registry=registry,
        format_checker=format_checker,
        self_digest_pointers=pointers,
        policies=base.policies,
        protocol_revision=base.protocol_revision,
    )


def _descriptor(
    *,
    schema_id: str,
    path: str,
    raw: bytes,
    schema_digest: str,
    self_pointer: str,
) -> Mapping[str, Any]:
    return {
        "schema_version": schema_id,
        "canonical_path": path,
        "content_digest": _sha256(raw),
        "schema_sha256": schema_digest,
        "self_digest_pointer": self_pointer,
    }


def build_readiness(
    *,
    disclosure: Mapping[str, Any],
    disclosure_schema: Mapping[str, Any],
    markdown_raw: bytes,
    predecessor: Mapping[str, Any],
    component_digest: str,
) -> Mapping[str, Any]:
    disclosure_raw = _render(disclosure)
    schema_raw = _render(disclosure_schema)
    readiness: Dict[str, Any] = {
        "schema_version": READINESS_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "status": (
            "DRAFT_NON_ACTIVE_GIT_HISTORY_PERSISTENCE_DISCLOSURE_READY"
        ),
        "owner_plane": "MECHANISM",
        "source_trust": {
            "candidate_bundle": {
                "verified_git_object_id": CANDIDATE_GIT_OBJECT,
                "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
                "canonical_path": CANDIDATE_MANIFEST_PATH,
                "artifact_digest": CANDIDATE_MANIFEST_RAW_SHA256,
                "expected_mode": "CANDIDATE",
                "schema_count": 31,
                "policy_count": 5,
            },
            "m063_predecessor": {
                "verified_git_object_id": M063_GIT_OBJECT,
                "readiness": {
                    "canonical_path": M063_READINESS_PATH,
                    "content_digest": M063_READINESS_RAW_SHA256,
                    "artifact_digest": M063_READINESS_SELF_DIGEST,
                },
                "component": {
                    "component_path": M063_COMPONENT_PATH,
                    "content_digest": M063_COMPONENT_RAW_SHA256,
                },
                "status": predecessor["status"],
                "done_gate": predecessor["task_contract"]["done_gate"],
            },
            "repository_self_report_is_not_trust_root": True,
        },
        "disclosure_contract": {
            "component_path": (
                "CodexSkills/governance/retention/"
                "git_history_disclosure.py"
            ),
            "content_digest": component_digest,
            "structured_disclosure": {
                "canonical_path": (
                    "CodexSkills/governance/retention/"
                    "git-history-persistence-disclosure.json"
                ),
                "content_digest": _sha256(disclosure_raw),
                "artifact_digest": disclosure["artifact_digest"],
            },
            "structured_disclosure_schema": _descriptor(
                schema_id=DISCLOSURE_SCHEMA_ID,
                path=(
                    "CodexSkills/governance/retention/schemas/"
                    "git-history-persistence-disclosure.schema.json"
                ),
                raw=schema_raw,
                schema_digest=canonical_digest(disclosure_schema),
                self_pointer=DISCLOSURE_SELF_POINTER,
            ),
            "markdown_disclosure": {
                "canonical_path": (
                    "CodexSkills/governance/retention/"
                    "GIT_HISTORY_PERSISTENCE_DISCLOSURE.md"
                ),
                "content_digest": _sha256(markdown_raw),
                "languages": ["en", "zh-CN"],
                "audiences": ["OPERATOR", "USER"],
            },
            "active_tree_scope": "GIT_CURRENT_TREE_ONLY",
            "receipt_proves_current_tree_transition_only": True,
            "git_history_may_retain_bytes_indefinitely": True,
            "fork_clone_cache_archive_backup_may_retain": True,
            "hard_deletion_claimed": False,
            "automatic_history_rewrite_permitted": False,
            "future_hard_erasure_design": (
                "OWNER_AUTHORIZED_MAJOR_REPOSITORY_ROTATION_OR_PRIVATE_STORAGE"
            ),
            "third_party_copy_deletion_guaranteed": False,
        },
        "surface_guard": {
            "mode": "READ_ONLY_BOUNDED_UTF8_SCAN",
            "declared_surface_roots": [
                {
                    "canonical_path": root,
                    "glob": "**/*.md",
                }
                for root in DISCLOSURE_SURFACE_ROOTS
            ],
            "positive_hard_erasure_claims_permitted": False,
            "exact_bilingual_disclosure_required": True,
            "ui_runtime_integration_status": "NOT_BOUND",
        },
        "nonmutation": {
            "auto_plane_unchanged": True,
            "openai_database_unchanged": True,
            "candidate_bundle_unchanged": True,
            "retention_policy_unchanged": True,
            "git_current_tree_artifact_removed": False,
            "git_history_rewrite_performed": False,
            "repository_rotation_performed": False,
            "private_storage_rotation_performed": False,
            "state_write_permitted": False,
            "canonical_publication_permitted": False,
            "activation_forbidden": True,
            "version_file_created": False,
        },
        "task_contract": {
            "dependency_task_ids": ["M-063"],
            "completed_task_ids": ["M-064"],
            "pending_task_ids": ["M-065"],
            "required_output": "OPERATOR_USER_DISCLOSURE",
            "done_gate": "SYSTEM_NEVER_CLAIMS_HARD_DELETION",
            "acceptance_criterion": "AC-19",
        },
        "schema_closure_count": 33,
        "policy_count": 5,
        "real_execution_permitted": False,
        "next_phase": NEXT_PHASE,
        "self_digest_pointer": "/artifact_digest",
        "task_pack_revision": "v0.0.0.2",
        "artifact_digest": "0" * 64,
    }
    readiness["artifact_digest"] = canonical_digest(
        readiness,
        "/artifact_digest",
    )
    return readiness


def build_readiness_schema(
    readiness: Mapping[str, Any],
) -> Mapping[str, Any]:
    properties: Dict[str, Any] = {
        key: {"const": value}
        for key, value in readiness.items()
        if key != "artifact_digest"
    }
    properties["artifact_digest"] = _ref("sha256")
    return {
        "$id": READINESS_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(readiness),
        "title": "Mechanism M-064 Git-history disclosure readiness",
        "type": "object",
    }


def _surface_paths() -> tuple[str, ...]:
    paths = []
    for relative_root in DISCLOSURE_SURFACE_ROOTS:
        root = REPO_ROOT.joinpath(*relative_root.split("/"))
        try:
            root.resolve().relative_to(REPO_ROOT.resolve())
        except ValueError as exc:
            raise GitHistoryDisclosureBuildError(
                "M064_DISCLOSURE_SURFACE_ROOT_INVALID:"
                + relative_root
            ) from exc
        if not root.is_dir() or root.is_symlink():
            raise GitHistoryDisclosureBuildError(
                "M064_DISCLOSURE_SURFACE_ROOT_INVALID:"
                + relative_root
            )
        for path in sorted(root.rglob("*.md"), key=lambda item: item.as_posix()):
            if not path.is_file() or path.is_symlink():
                raise GitHistoryDisclosureBuildError(
                    "M064_DISCLOSURE_SURFACE_FILE_INVALID:"
                    + str(path.relative_to(REPO_ROOT))
                )
            paths.append(path.relative_to(REPO_ROOT).as_posix())
    paths.append(CANONICAL_DISCLOSURE_PATH)
    return tuple(sorted(set(paths)))


def _scan_declared_surfaces(markdown_raw: bytes) -> tuple[str, ...]:
    paths = _surface_paths()
    for relative_path in paths:
        raw = (
            markdown_raw
            if relative_path == CANONICAL_DISCLOSURE_PATH
            else _current(relative_path)
        )
        validate_disclosure_surface(relative_path, raw)
    return paths


def _documents() -> Mapping[Path, bytes]:
    predecessor = _validate_predecessor()
    acceptance = load_au040_acceptance()
    if (
        len(acceptance.bundle.schemas) != 31
        or len(acceptance.bundle.policies) != 5
        or acceptance.bundle.protocol_revision != PROTOCOL_REVISION
    ):
        raise GitHistoryDisclosureBuildError(
            "M064_CANDIDATE_CONTRACT_INVALID"
        )
    disclosure = build_disclosure()
    validate_disclosure(disclosure)
    markdown_raw = render_disclosure_markdown()
    validate_disclosure_markdown(markdown_raw)
    disclosure_schema = build_disclosure_schema(disclosure)
    disclosure_contract = _extend_bundle(
        acceptance.bundle,
        {DISCLOSURE_SCHEMA_ID: disclosure_schema},
        {DISCLOSURE_SCHEMA_ID: DISCLOSURE_SELF_POINTER},
    )
    try:
        validate_instance(
            disclosure_contract,
            disclosure,
            DISCLOSURE_SCHEMA_ID,
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            verify_digest=True,
            public=True,
        )
    except ContractError as exc:
        raise GitHistoryDisclosureBuildError(
            "M064_DISCLOSURE_INVALID:" + str(exc)
        ) from exc
    component_digest = _sha256(COMPONENT_PATH.read_bytes())
    readiness = build_readiness(
        disclosure=disclosure,
        disclosure_schema=disclosure_schema,
        markdown_raw=markdown_raw,
        predecessor=predecessor,
        component_digest=component_digest,
    )
    readiness_schema = build_readiness_schema(readiness)
    final_contract = _extend_bundle(
        disclosure_contract,
        {READINESS_SCHEMA_ID: readiness_schema},
        {READINESS_SCHEMA_ID: "/artifact_digest"},
    )
    if len(final_contract.schemas) != 33:
        raise GitHistoryDisclosureBuildError(
            "M064_SCHEMA_CLOSURE_COUNT_INVALID"
        )
    try:
        validate_instance(
            final_contract,
            readiness,
            READINESS_SCHEMA_ID,
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            verify_digest=True,
            public=True,
        )
        scan_public_value(disclosure, final_contract.policies)
    except ContractError as exc:
        raise GitHistoryDisclosureBuildError(
            "M064_READINESS_INVALID:" + str(exc)
        ) from exc
    _scan_declared_surfaces(markdown_raw)
    return {
        DISCLOSURE_MARKDOWN_PATH: markdown_raw,
        DISCLOSURE_PATH: _render(disclosure),
        DISCLOSURE_SCHEMA_PATH: _render(disclosure_schema),
        READINESS_PATH: _render(readiness),
        READINESS_SCHEMA_PATH: _render(readiness_schema),
    }


def _write() -> None:
    documents = _documents()
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    for path, raw in documents.items():
        path.write_bytes(raw)


def _check() -> None:
    documents = _documents()
    for path, expected in documents.items():
        if not path.is_file() or path.is_symlink():
            raise GitHistoryDisclosureBuildError(
                "M064_ARTIFACT_FILE_INVALID:"
                + str(path.relative_to(REPO_ROOT))
            )
        if path.read_bytes() != expected:
            raise GitHistoryDisclosureBuildError(
                "M064_ARTIFACT_NOT_BYTE_EQUIVALENT:"
                + str(path.relative_to(REPO_ROOT))
            )
    if VERSION_PATH.exists():
        raise GitHistoryDisclosureBuildError(
            "M064_ACTIVE_VERSION_FORBIDDEN"
        )


def _main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        _write()
    else:
        _check()
    print(
        "GIT_HISTORY_PERSISTENCE_DISCLOSURE_OK "
        "current_tree_only=true hard_deletion_claimed=false "
        "history_rewrite=false ui_integration=NOT_BOUND"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except (
        ContractError,
        GitHistoryDisclosureError,
        GitHistoryDisclosureBuildError,
    ) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
