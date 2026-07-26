#!/usr/bin/env python3
"""Build/check non-active Mechanism M-056 promotion-controller evidence."""

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

from CodexSkills.governance.promotion.controller import (  # noqa: E402
    PROTOCOL_REVISION,
    build_registry_view,
)
from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_mechanism import (  # noqa: E402
    ContractError,
    Draft202012Validator,
    TrustTuple,
    lint_schema_documents,
    load_trusted_bundle,
    scan_public_value,
)


GOVERNANCE_DIR = REPO_ROOT / "CodexSkills" / "governance"
PROMOTION_DIR = GOVERNANCE_DIR / "promotion"
OUTPUT_PATH = PROMOTION_DIR / "controller-readiness.json"
SCHEMA_PATH = (
    PROMOTION_DIR
    / "schemas"
    / "promotion-controller-readiness.schema.json"
)
CONTROLLER_PATH = PROMOTION_DIR / "controller.py"
REGISTRY_SNAPSHOT_PATH = (
    REPO_ROOT
    / "CodexSkills"
    / "registry"
    / "_global"
    / "registry-snapshot.v1.json"
)
VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

READINESS_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:promotion-controller-readiness:v1"
)
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
REGISTRY_SNAPSHOT_GIT_OBJECT = (
    "sha1:98e193e74991346d266bdd94ae720c32f25dfb47"
)
REGISTRY_SNAPSHOT_REPO_PATH = (
    "CodexSkills/registry/_global/registry-snapshot.v1.json"
)
REGISTRY_SNAPSHOT_RAW_SHA256 = (
    "ed5fb74fa88a2f1115a716be5e63f683d206c10d3d0a2005230d4c33d4c12c98"
)
NEXT_PHASE = "MECHANISM_ROLLBACK_REVOCATION_CONTROLLER"


class PromotionControllerBuildError(ValueError):
    """Readiness material cannot be reproduced without weakening a gate."""


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


def _load(path: Path) -> Mapping[str, Any]:
    try:
        value = parse_json_bytes(path.read_bytes())
    except Exception as exc:
        raise PromotionControllerBuildError(
            "PROMOTION_CONTROLLER_JSON_INVALID:" + path.as_posix()
        ) from exc
    if not isinstance(value, dict):
        raise PromotionControllerBuildError(
            "PROMOTION_CONTROLLER_JSON_ROOT_INVALID:" + path.as_posix()
        )
    return value


def _git_blob(tagged_object: str, relative_path: str) -> bytes:
    if tagged_object.count(":") != 1:
        raise PromotionControllerBuildError(
            "PROMOTION_CONTROLLER_GIT_OBJECT_INVALID"
        )
    _, object_id = tagged_object.split(":", 1)
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
        raise PromotionControllerBuildError(
            "PROMOTION_CONTROLLER_GIT_UNAVAILABLE"
        ) from exc
    if process.returncode != 0:
        raise PromotionControllerBuildError(
            "PROMOTION_CONTROLLER_GIT_BLOB_UNAVAILABLE:" + relative_path
        )
    return process.stdout


def _ref(name: str) -> Dict[str, str]:
    return {
        "$ref": (
            "urn:linzecolin:agentdatabase:skillops:"
            "schema:common-definitions:v1#/$defs/"
            + name
        )
    }


def _closed(
    properties: Mapping[str, Any],
    required: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": dict(properties),
        "required": list(required or properties),
        "type": "object",
    }


def build_schema() -> Mapping[str, Any]:
    candidate_trust = _closed(
        {
            "artifact_digest": _ref("sha256"),
            "bundle_digest": _ref("sha256"),
            "canonical_path": {
                "const": CANDIDATE_MANIFEST_PATH,
            },
            "expected_mode": {"const": "CANDIDATE"},
            "policy_count": {"const": 5},
            "schema_count": {"const": 31},
            "verified_git_object_id": _ref("git_object_id"),
        }
    )
    snapshot_trust = _closed(
        {
            "artifact_digest": _ref("sha256"),
            "canonical_path": {
                "const": REGISTRY_SNAPSHOT_REPO_PATH,
            },
            "digest_basis": {"const": "RAW_BYTES"},
            "expected_mode": {"const": "REGISTERED_READ_ONLY"},
            "registry_snapshot_digest": _ref("sha256"),
            "verified_git_object_id": _ref("git_object_id"),
        }
    )
    controller_contract = _closed(
        {
            "append_record_format": {
                "const": "RFC8785_JCS_UTF8_NO_BOM_NO_LF",
            },
            "candidate_bundle_trust_required": {"const": True},
            "complete_reference_closure_required": {"const": True},
            "component_source_binding_mode": {
                "const": "SUCCESSOR_EXTERNAL_TUPLE_REQUIRED",
            },
            "content_digest": _ref("sha256"),
            "component_path": {
                "const": (
                    "CodexSkills/governance/promotion/controller.py"
                )
            },
            "decision_actions": {
                "const": ["PROMOTE", "REJECT"],
            },
            "decision_uid_and_digest_unique": {"const": True},
            "evidence_reuse_permitted": {"const": False},
            "external_predecessor_ledger_digest_required": {
                "const": True,
            },
            "ledger_digest_domain": {
                "const": "SKILLOPS_PROMOTION_LEDGER_V1",
            },
            "m056_no_gate_bypass_verified": {"const": True},
            "m056_one_champion_per_scope_verified": {"const": True},
            "public_artifact_write_permitted": {"const": False},
            "promotion_transition": {
                "const": "CHALLENGER_TO_CHAMPION",
            },
            "reject_transition": {
                "const": "CHALLENGER_TO_QUARANTINED_STAGE_REJECTED",
            },
            "rollback_revocation_actions": {
                "const": ["ROLLBACK", "REVOKE"],
            },
            "rollback_revocation_implemented": {"const": False},
            "state_write_permitted": {"const": False},
            "strict_time_order_required": {"const": True},
        }
    )
    observation = _closed(
        {
            "base_champion_count": _ref("nonnegative_count"),
            "challenger_version_count": _ref("nonnegative_count"),
            "identity_count": _ref("nonnegative_count"),
            "instance_count": _ref("nonnegative_count"),
            "real_promotion_execution_permitted": {"const": False},
            "reason_code": {
                "const": "NO_REGISTERED_CHALLENGER_OR_CHAMPION",
            },
            "snapshot_status": {"const": "REGISTERED"},
            "version_count": _ref("nonnegative_count"),
        }
    )
    nonmutation = _closed(
        {
            "activation_forbidden": {"const": True},
            "auto_plane_unchanged": {"const": True},
            "candidate_bundle_unchanged": {"const": True},
            "canonical_publication_permitted": {"const": False},
            "registry_write_permitted": {"const": False},
            "rollback_revocation_execution_permitted": {"const": False},
            "version_file_created": {"const": False},
        }
    )
    task_contract = _closed(
        {
            "completed_task_ids": {"const": ["M-056"]},
            "done_gate": {
                "const": "NO_GATE_BYPASS_AND_ONE_CHAMPION_PER_SCOPE",
            },
            "pending_task_ids": {"const": ["M-057"]},
            "required_output": {
                "const": "APPEND_ONLY_CHAMPION_REJECT_DECISION",
            },
        }
    )
    return {
        "$id": READINESS_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "artifact_digest": _ref("sha256"),
            "controller_contract": controller_contract,
            "digest_algorithm": {"const": "SHA-256"},
            "next_phase": {"const": NEXT_PHASE},
            "nonmutation": nonmutation,
            "owner_plane": {"const": "MECHANISM"},
            "protocol_revision": _ref("protocol_revision"),
            "registry_observation": observation,
            "schema_version": {"const": READINESS_SCHEMA_ID},
            "self_digest_pointer": {"const": "/artifact_digest"},
            "source_trust": _closed(
                {
                    "candidate_bundle": candidate_trust,
                    "registry_snapshot": snapshot_trust,
                    "repository_self_report_is_not_trust_root": {
                        "const": True,
                    },
                }
            ),
            "status": {
                "const": "DRAFT_NON_ACTIVE_PROMOTION_CONTROLLER_READY",
            },
            "task_contract": task_contract,
            "task_pack_revision": {"const": "v0.0.0.2"},
        },
        "required": [
            "artifact_digest",
            "controller_contract",
            "digest_algorithm",
            "next_phase",
            "nonmutation",
            "owner_plane",
            "protocol_revision",
            "registry_observation",
            "schema_version",
            "self_digest_pointer",
            "source_trust",
            "status",
            "task_contract",
            "task_pack_revision",
        ],
        "title": "Mechanism M-056 promotion-controller readiness",
        "type": "object",
    }


def build_readiness() -> Mapping[str, Any]:
    candidate_trust = TrustTuple(
        verified_git_object_id=CANDIDATE_GIT_OBJECT,
        expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
        canonical_manifest_path=CANDIDATE_MANIFEST_PATH,
        mode="CANDIDATE",
    )
    candidate_manifest_raw = _git_blob(
        CANDIDATE_GIT_OBJECT,
        CANDIDATE_MANIFEST_PATH,
    )
    if _sha256(candidate_manifest_raw) != CANDIDATE_MANIFEST_RAW_SHA256:
        raise PromotionControllerBuildError(
            "PROMOTION_CONTROLLER_CANDIDATE_MANIFEST_RAW_MISMATCH"
        )
    bundle = load_trusted_bundle(REPO_ROOT, candidate_trust)

    snapshot_raw = REGISTRY_SNAPSHOT_PATH.read_bytes()
    if (
        _sha256(snapshot_raw) != REGISTRY_SNAPSHOT_RAW_SHA256
        or _git_blob(
            REGISTRY_SNAPSHOT_GIT_OBJECT,
            REGISTRY_SNAPSHOT_REPO_PATH,
        )
        != snapshot_raw
    ):
        raise PromotionControllerBuildError(
            "PROMOTION_CONTROLLER_REGISTRY_SNAPSHOT_TRUST_MISMATCH"
        )
    snapshot = _load(REGISTRY_SNAPSHOT_PATH)
    registry_view = build_registry_view(
        bundle,
        snapshot,
        expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
        expected_registry_snapshot_digest=snapshot[
            "registry_snapshot_digest"
        ],
    )
    if registry_view.base_champions or registry_view.challenger_version_uids:
        raise PromotionControllerBuildError(
            "PROMOTION_CONTROLLER_REAL_REGISTRY_NOT_QUIESCENT"
        )
    if VERSION_PATH.exists():
        raise PromotionControllerBuildError(
            "PROMOTION_CONTROLLER_ACTIVE_VERSION_FORBIDDEN"
        )

    readiness: Dict[str, Any] = {
        "artifact_digest": "0" * 64,
        "controller_contract": {
            "append_record_format": "RFC8785_JCS_UTF8_NO_BOM_NO_LF",
            "candidate_bundle_trust_required": True,
            "complete_reference_closure_required": True,
            "component_source_binding_mode": (
                "SUCCESSOR_EXTERNAL_TUPLE_REQUIRED"
            ),
            "content_digest": _sha256(
                CONTROLLER_PATH.read_bytes()
            ),
            "component_path": (
                "CodexSkills/governance/promotion/controller.py"
            ),
            "decision_actions": ["PROMOTE", "REJECT"],
            "decision_uid_and_digest_unique": True,
            "evidence_reuse_permitted": False,
            "external_predecessor_ledger_digest_required": True,
            "ledger_digest_domain": "SKILLOPS_PROMOTION_LEDGER_V1",
            "m056_no_gate_bypass_verified": True,
            "m056_one_champion_per_scope_verified": True,
            "public_artifact_write_permitted": False,
            "promotion_transition": "CHALLENGER_TO_CHAMPION",
            "reject_transition": (
                "CHALLENGER_TO_QUARANTINED_STAGE_REJECTED"
            ),
            "rollback_revocation_actions": ["ROLLBACK", "REVOKE"],
            "rollback_revocation_implemented": False,
            "state_write_permitted": False,
            "strict_time_order_required": True,
        },
        "digest_algorithm": "SHA-256",
        "next_phase": NEXT_PHASE,
        "nonmutation": {
            "activation_forbidden": True,
            "auto_plane_unchanged": True,
            "candidate_bundle_unchanged": True,
            "canonical_publication_permitted": False,
            "registry_write_permitted": False,
            "rollback_revocation_execution_permitted": False,
            "version_file_created": False,
        },
        "owner_plane": "MECHANISM",
        "protocol_revision": PROTOCOL_REVISION,
        "registry_observation": {
            "base_champion_count": len(registry_view.base_champions),
            "challenger_version_count": len(
                registry_view.challenger_version_uids
            ),
            "identity_count": len(registry_view.identity_uids),
            "instance_count": len(registry_view.instance_bindings),
            "real_promotion_execution_permitted": False,
            "reason_code": "NO_REGISTERED_CHALLENGER_OR_CHAMPION",
            "snapshot_status": snapshot["status"],
            "version_count": len(registry_view.versions),
        },
        "schema_version": READINESS_SCHEMA_ID,
        "self_digest_pointer": "/artifact_digest",
        "source_trust": {
            "candidate_bundle": {
                "artifact_digest": CANDIDATE_MANIFEST_RAW_SHA256,
                "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
                "canonical_path": CANDIDATE_MANIFEST_PATH,
                "expected_mode": "CANDIDATE",
                "policy_count": len(bundle.policies),
                "schema_count": len(bundle.schemas),
                "verified_git_object_id": CANDIDATE_GIT_OBJECT,
            },
            "registry_snapshot": {
                "artifact_digest": REGISTRY_SNAPSHOT_RAW_SHA256,
                "canonical_path": REGISTRY_SNAPSHOT_REPO_PATH,
                "digest_basis": "RAW_BYTES",
                "expected_mode": "REGISTERED_READ_ONLY",
                "registry_snapshot_digest": (
                    registry_view.registry_snapshot_digest
                ),
                "verified_git_object_id": (
                    REGISTRY_SNAPSHOT_GIT_OBJECT
                ),
            },
            "repository_self_report_is_not_trust_root": True,
        },
        "status": "DRAFT_NON_ACTIVE_PROMOTION_CONTROLLER_READY",
        "task_contract": {
            "completed_task_ids": ["M-056"],
            "done_gate": "NO_GATE_BYPASS_AND_ONE_CHAMPION_PER_SCOPE",
            "pending_task_ids": ["M-057"],
            "required_output": "APPEND_ONLY_CHAMPION_REJECT_DECISION",
        },
        "task_pack_revision": "v0.0.0.2",
    }
    readiness["artifact_digest"] = canonical_digest(
        readiness,
        "/artifact_digest",
    )
    validate_readiness(bundle, build_schema(), readiness)
    return readiness


def validate_readiness(
    bundle: Any,
    schema: Mapping[str, Any],
    readiness: Mapping[str, Any],
) -> None:
    schemas = dict(bundle.schemas)
    schemas[READINESS_SCHEMA_ID] = schema
    try:
        lint_schema_documents(schemas)
        errors = sorted(
            Draft202012Validator(
                schema,
                registry=bundle.registry,
                format_checker=bundle.format_checker,
            ).iter_errors(readiness),
            key=lambda item: tuple(
                str(piece) for piece in item.absolute_path
            ),
        )
    except ContractError as exc:
        raise PromotionControllerBuildError(
            "PROMOTION_CONTROLLER_READINESS_SCHEMA_CLOSURE_INVALID:"
            + str(exc)
        ) from exc
    if errors:
        raise PromotionControllerBuildError(
            "PROMOTION_CONTROLLER_READINESS_SCHEMA_INVALID:"
            + " | ".join(error.message for error in errors)
        )
    if readiness.get("artifact_digest") != canonical_digest(
        readiness,
        "/artifact_digest",
    ):
        raise PromotionControllerBuildError(
            "PROMOTION_CONTROLLER_READINESS_DIGEST_MISMATCH"
        )
    try:
        scan_public_value(readiness, bundle.policies)
    except ContractError as exc:
        raise PromotionControllerBuildError(
            "PROMOTION_CONTROLLER_READINESS_PRIVACY_INVALID:" + str(exc)
        ) from exc


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    schema_raw = _render(build_schema())
    readiness_raw = _render(build_readiness())
    expected = {
        SCHEMA_PATH: schema_raw,
        OUTPUT_PATH: readiness_raw,
    }
    if args.write:
        for path, raw in expected.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        action = "PROMOTION_CONTROLLER_GENERATED"
    else:
        mismatches = [
            path.as_posix()
            for path, raw in expected.items()
            if not path.is_file() or path.read_bytes() != raw
        ]
        if mismatches:
            raise PromotionControllerBuildError(
                "PROMOTION_CONTROLLER_BYTE_DRIFT:" + ",".join(mismatches)
            )
        action = "PROMOTION_CONTROLLER_BYTE_EQUIVALENT"
    print(
        action
        + " "
        + "artifact_digest="
        + build_readiness()["artifact_digest"]
        + " "
        + "registry_versions=89 "
        + "real_challengers=0 real_champions=0"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PromotionControllerBuildError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
