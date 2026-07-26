#!/usr/bin/env python3
"""Build/check non-active Mechanism M-057 rollback-controller evidence."""

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
from CodexSkills.governance.promotion.rollback_controller import (  # noqa: E402
    LIFECYCLE_LEDGER_DOMAIN,
    REQUIRED_VERIFICATION_KINDS,
    ROLLBACK_DRILL_SCHEMA_ID,
    ROLLBACK_DRILL_SELF_POINTER,
    RollbackControllerError,
    build_rollback_contract,
)
from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_mechanism import (  # noqa: E402
    ContractBundle,
    ContractError,
    TrustTuple,
    build_registry,
    load_trusted_bundle,
    scan_public_value,
    validate_instance,
)


GOVERNANCE_DIR = REPO_ROOT / "CodexSkills" / "governance"
PROMOTION_DIR = GOVERNANCE_DIR / "promotion"
OUTPUT_PATH = PROMOTION_DIR / "rollback-controller-readiness.json"
DRILL_SCHEMA_PATH = (
    PROMOTION_DIR / "schemas" / "rollback-drill-evidence.schema.json"
)
READINESS_SCHEMA_PATH = (
    PROMOTION_DIR / "schemas" / "rollback-controller-readiness.schema.json"
)
CONTROLLER_PATH = PROMOTION_DIR / "rollback_controller.py"
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
    "schema:rollback-controller-readiness:v1"
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
M056_GIT_OBJECT = (
    "sha1:3cc02c15359d5204ad34fc9c20edbc02ec3802f0"
)
M056_CONTROLLER_PATH = (
    "CodexSkills/governance/promotion/controller.py"
)
M056_CONTROLLER_RAW_SHA256 = (
    "bcc39aaa1e6c817fb321a8772996a05fffffe947cd8bbc218a5f7bad16db3e53"
)
M056_READINESS_PATH = (
    "CodexSkills/governance/promotion/controller-readiness.json"
)
M056_READINESS_RAW_SHA256 = (
    "d54d577bf53e155c1eb6215db388d9f7939f91e21d6af938242c49928b44d1ae"
)
NEXT_PHASE = "MECHANISM_FRESHNESS_DRIFT_MONITOR"


class RollbackControllerBuildError(ValueError):
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
    except RollbackControllerError as exc:
        raise RollbackControllerBuildError(
            "ROLLBACK_CONTROLLER_JSON_INVALID:" + path.as_posix()
        ) from exc
    if not isinstance(value, dict):
        raise RollbackControllerBuildError(
            "ROLLBACK_CONTROLLER_JSON_ROOT_INVALID:" + path.as_posix()
        )
    return value


def _git_blob(tagged_object: str, relative_path: str) -> bytes:
    if tagged_object.count(":") != 1:
        raise RollbackControllerBuildError(
            "ROLLBACK_CONTROLLER_GIT_OBJECT_INVALID"
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
        raise RollbackControllerBuildError(
            "ROLLBACK_CONTROLLER_GIT_UNAVAILABLE"
        ) from exc
    if process.returncode != 0:
        raise RollbackControllerBuildError(
            "ROLLBACK_CONTROLLER_GIT_BLOB_UNAVAILABLE:" + relative_path
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


def _nullable(value: Mapping[str, Any]) -> Dict[str, Any]:
    return {"anyOf": [dict(value), {"type": "null"}]}


def build_drill_schema() -> Mapping[str, Any]:
    champion_ref = _closed(
        {
            "decision_digest": _nullable(_ref("sha256")),
            "model_snapshot_digest": _ref("sha256"),
            "skill_version_uid": _ref("skill_version_uid"),
            "version_record_digest": _ref("sha256"),
        }
    )
    predecessor = _closed(
        {
            "artifact_digest": _ref("sha256"),
            "decision_count": _ref("nonnegative_count"),
        }
    )
    verification_ref = _closed(
        {
            "artifact_digest": _ref("sha256"),
            "kind": {"enum": list(REQUIRED_VERIFICATION_KINDS)},
        }
    )
    containment = _nullable(
        _closed({"evidence_digest": _ref("sha256")})
    )
    properties = {
        "action": {"enum": ["ROLLBACK", "REVOKE"]},
        "actor": {"const": "SKILLOPS_ROLLBACK_CONTROLLER"},
        "bundle_digest": _ref("sha256"),
        "completed_at": _ref("utc_z_timestamp"),
        "containment_evidence": containment,
        "current_champion_ref": champion_ref,
        "drill_status": {"const": "PASS"},
        "environment_fingerprint_digest": _ref("sha256"),
        "evidence_bundle_digest": _ref("sha256"),
        "execution_mode": {
            "enum": [
                "PLANNED_PRE_WRITE",
                "EMERGENCY_POST_CONTAINMENT",
            ]
        },
        "history_rewrite_performed": {"const": False},
        "known_risk_codes": {
            "items": _ref("enum_code"),
            "type": "array",
            "uniqueItems": True,
        },
        "notification_mode": {
            "enum": ["PRE_WRITE_SENT", "POST_CONTAINMENT_SENT"],
        },
        "notification_receipt_digest": _ref("sha256"),
        "policy_snapshot_digest": _ref("sha256"),
        "predecessor_ledger": predecessor,
        "protocol_revision": _ref("protocol_revision"),
        "registry_snapshot_digest": _ref("sha256"),
        "restore_target_content_verified": {"const": True},
        "restore_target_reference_closure_verified": {"const": True},
        "rollback_drill_uid": _ref("typed_uid"),
        "rollback_target_ref": champion_ref,
        "rollback_target_restorable": {"const": True},
        "schema_version": {"const": ROLLBACK_DRILL_SCHEMA_ID},
        "skill_identity_uid": _ref("skill_identity_uid"),
        "state_write_observed": {"type": "boolean"},
        "trigger_codes": {
            "items": _ref("enum_code"),
            "minItems": 1,
            "type": "array",
            "uniqueItems": True,
        },
        "verification_evidence_refs": {
            "items": verification_ref,
            "minItems": len(REQUIRED_VERIFICATION_KINDS),
            "type": "array",
            "uniqueItems": True,
        },
    }
    return {
        "$id": ROLLBACK_DRILL_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
        "title": "Rollback or revocation restore-drill evidence",
        "type": "object",
    }


def build_readiness_schema() -> Mapping[str, Any]:
    candidate_trust = _closed(
        {
            "artifact_digest": _ref("sha256"),
            "bundle_digest": _ref("sha256"),
            "canonical_path": {"const": CANDIDATE_MANIFEST_PATH},
            "expected_mode": {"const": "CANDIDATE"},
            "policy_count": {"const": 5},
            "schema_count": {"const": 31},
            "verified_git_object_id": _ref("git_object_id"),
        }
    )
    snapshot_trust = _closed(
        {
            "artifact_digest": _ref("sha256"),
            "canonical_path": {"const": REGISTRY_SNAPSHOT_REPO_PATH},
            "expected_mode": {"const": "REGISTERED_READ_ONLY"},
            "registry_snapshot_digest": _ref("sha256"),
            "verified_git_object_id": _ref("git_object_id"),
        }
    )
    m056_trust = _closed(
        {
            "artifact_digest": _ref("sha256"),
            "canonical_path": {"const": M056_CONTROLLER_PATH},
            "expected_mode": {"const": "M056_IMMUTABLE_PREDECESSOR"},
            "readiness_artifact": _closed(
                {
                    "artifact_digest": _ref("sha256"),
                    "canonical_path": {"const": M056_READINESS_PATH},
                }
            ),
            "verified_git_object_id": _ref("git_object_id"),
        }
    )
    drill_contract = _closed(
        {
            "artifact_digest": _ref("sha256"),
            "canonical_path": {
                "const": (
                    "CodexSkills/governance/promotion/schemas/"
                    "rollback-drill-evidence.schema.json"
                )
            },
            "schema_sha256": _ref("sha256"),
            "schema_version": {"const": ROLLBACK_DRILL_SCHEMA_ID},
            "self_digest_pointer": {"const": ROLLBACK_DRILL_SELF_POINTER},
        }
    )
    controller_contract = _closed(
        {
            "append_record_format": {
                "const": "RFC8785_JCS_UTF8_NO_BOM_NO_LF",
            },
            "component_path": {
                "const": (
                    "CodexSkills/governance/promotion/"
                    "rollback_controller.py"
                )
            },
            "component_source_binding_mode": {
                "const": "SUCCESSOR_EXTERNAL_TUPLE_REQUIRED",
            },
            "content_digest": _ref("sha256"),
            "decision_actions": {
                "const": ["PROMOTE", "REJECT", "ROLLBACK", "REVOKE"],
            },
            "emergency_notification_order": {
                "const": "CONTAINMENT_THEN_POST_CONTAINMENT_SENT",
            },
            "external_predecessor_ledger_digest_required": {
                "const": True,
            },
            "history_rewrite_permitted": {"const": False},
            "lifecycle_ledger_domain": {
                "const": LIFECYCLE_LEDGER_DOMAIN,
            },
            "m056_promotion_step_delegation_required": {"const": True},
            "planned_notification_order": {
                "const": "PRE_WRITE_SENT_THEN_EVENT",
            },
            "prior_champion_proof_source": {
                "const": "BASE_CHAMPION_PLUS_ORDERED_PRIOR_EVENTS",
            },
            "public_artifact_write_permitted": {"const": False},
            "revoked_target_restore_permitted": {"const": False},
            "rollback_drill_schema": drill_contract,
            "state_write_permitted": {"const": False},
        }
    )
    observation = _closed(
        {
            "base_champion_count": _ref("nonnegative_count"),
            "challenger_version_count": _ref("nonnegative_count"),
            "identity_count": _ref("nonnegative_count"),
            "instance_count": _ref("nonnegative_count"),
            "reason_code": {
                "const": "NO_REGISTERED_CHAMPION_TO_ROLLBACK_OR_REVOKE",
            },
            "real_rollback_revocation_execution_permitted": {
                "const": False,
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
            "completed_task_ids": {"const": ["M-056", "M-057"]},
            "done_gate": {
                "const": "NO_HISTORY_REWRITE_AND_PRIOR_CHAMPION_RESTORABLE",
            },
            "pending_task_ids": {"const": ["M-058"]},
            "required_output": {
                "const": "NEW_EVENT_ROLLBACK_AND_DRILL_EVIDENCE",
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
                    "m056_controller": m056_trust,
                    "registry_snapshot": snapshot_trust,
                    "repository_self_report_is_not_trust_root": {
                        "const": True,
                    },
                }
            ),
            "status": {
                "const": (
                    "DRAFT_NON_ACTIVE_ROLLBACK_REVOCATION_CONTROLLER_READY"
                ),
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
        "title": "Mechanism M-057 rollback-controller readiness",
        "type": "object",
    }


def _trusted_candidate() -> ContractBundle:
    manifest_raw = _git_blob(
        CANDIDATE_GIT_OBJECT,
        CANDIDATE_MANIFEST_PATH,
    )
    if _sha256(manifest_raw) != CANDIDATE_MANIFEST_RAW_SHA256:
        raise RollbackControllerBuildError(
            "ROLLBACK_CONTROLLER_CANDIDATE_MANIFEST_RAW_MISMATCH"
        )
    return load_trusted_bundle(
        REPO_ROOT,
        TrustTuple(
            verified_git_object_id=CANDIDATE_GIT_OBJECT,
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            canonical_manifest_path=CANDIDATE_MANIFEST_PATH,
            mode="CANDIDATE",
        ),
    )


def build_readiness() -> Mapping[str, Any]:
    bundle = _trusted_candidate()
    drill_schema = build_drill_schema()
    drill_schema_digest = canonical_digest(drill_schema)
    try:
        build_rollback_contract(
            bundle,
            drill_schema,
            drill_schema_digest,
        )
    except Exception as exc:
        raise RollbackControllerBuildError(
            "ROLLBACK_CONTROLLER_DRILL_SCHEMA_INVALID:" + str(exc)
        ) from exc

    snapshot_raw = REGISTRY_SNAPSHOT_PATH.read_bytes()
    if (
        _sha256(snapshot_raw) != REGISTRY_SNAPSHOT_RAW_SHA256
        or _git_blob(
            REGISTRY_SNAPSHOT_GIT_OBJECT,
            REGISTRY_SNAPSHOT_REPO_PATH,
        )
        != snapshot_raw
    ):
        raise RollbackControllerBuildError(
            "ROLLBACK_CONTROLLER_REGISTRY_SNAPSHOT_TRUST_MISMATCH"
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
    if registry_view.base_champions:
        raise RollbackControllerBuildError(
            "ROLLBACK_CONTROLLER_REAL_REGISTRY_HAS_CHAMPION"
        )
    if VERSION_PATH.exists():
        raise RollbackControllerBuildError(
            "ROLLBACK_CONTROLLER_ACTIVE_VERSION_FORBIDDEN"
        )
    if (
        _sha256(_git_blob(M056_GIT_OBJECT, M056_CONTROLLER_PATH))
        != M056_CONTROLLER_RAW_SHA256
        or _git_blob(M056_GIT_OBJECT, M056_CONTROLLER_PATH)
        != (PROMOTION_DIR / "controller.py").read_bytes()
        or _sha256(_git_blob(M056_GIT_OBJECT, M056_READINESS_PATH))
        != M056_READINESS_RAW_SHA256
    ):
        raise RollbackControllerBuildError(
            "ROLLBACK_CONTROLLER_M056_PREDECESSOR_TRUST_MISMATCH"
        )

    drill_schema_raw = _render(drill_schema)
    readiness: Dict[str, Any] = {
        "artifact_digest": "0" * 64,
        "controller_contract": {
            "append_record_format": "RFC8785_JCS_UTF8_NO_BOM_NO_LF",
            "component_path": (
                "CodexSkills/governance/promotion/rollback_controller.py"
            ),
            "component_source_binding_mode": (
                "SUCCESSOR_EXTERNAL_TUPLE_REQUIRED"
            ),
            "content_digest": _sha256(CONTROLLER_PATH.read_bytes()),
            "decision_actions": [
                "PROMOTE",
                "REJECT",
                "ROLLBACK",
                "REVOKE",
            ],
            "emergency_notification_order": (
                "CONTAINMENT_THEN_POST_CONTAINMENT_SENT"
            ),
            "external_predecessor_ledger_digest_required": True,
            "history_rewrite_permitted": False,
            "lifecycle_ledger_domain": LIFECYCLE_LEDGER_DOMAIN,
            "m056_promotion_step_delegation_required": True,
            "planned_notification_order": "PRE_WRITE_SENT_THEN_EVENT",
            "prior_champion_proof_source": (
                "BASE_CHAMPION_PLUS_ORDERED_PRIOR_EVENTS"
            ),
            "public_artifact_write_permitted": False,
            "revoked_target_restore_permitted": False,
            "rollback_drill_schema": {
                "artifact_digest": _sha256(drill_schema_raw),
                "canonical_path": (
                    "CodexSkills/governance/promotion/schemas/"
                    "rollback-drill-evidence.schema.json"
                ),
                "schema_sha256": drill_schema_digest,
                "schema_version": ROLLBACK_DRILL_SCHEMA_ID,
                "self_digest_pointer": ROLLBACK_DRILL_SELF_POINTER,
            },
            "state_write_permitted": False,
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
            "reason_code": (
                "NO_REGISTERED_CHAMPION_TO_ROLLBACK_OR_REVOKE"
            ),
            "real_rollback_revocation_execution_permitted": False,
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
            "m056_controller": {
                "artifact_digest": M056_CONTROLLER_RAW_SHA256,
                "canonical_path": M056_CONTROLLER_PATH,
                "expected_mode": "M056_IMMUTABLE_PREDECESSOR",
                "readiness_artifact": {
                    "artifact_digest": M056_READINESS_RAW_SHA256,
                    "canonical_path": M056_READINESS_PATH,
                },
                "verified_git_object_id": M056_GIT_OBJECT,
            },
            "registry_snapshot": {
                "artifact_digest": REGISTRY_SNAPSHOT_RAW_SHA256,
                "canonical_path": REGISTRY_SNAPSHOT_REPO_PATH,
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
        "status": (
            "DRAFT_NON_ACTIVE_ROLLBACK_REVOCATION_CONTROLLER_READY"
        ),
        "task_contract": {
            "completed_task_ids": ["M-056", "M-057"],
            "done_gate": (
                "NO_HISTORY_REWRITE_AND_PRIOR_CHAMPION_RESTORABLE"
            ),
            "pending_task_ids": ["M-058"],
            "required_output": (
                "NEW_EVENT_ROLLBACK_AND_DRILL_EVIDENCE"
            ),
        },
        "task_pack_revision": "v0.0.0.2",
    }
    readiness["artifact_digest"] = canonical_digest(
        readiness,
        "/artifact_digest",
    )
    validate_readiness(bundle, drill_schema, readiness)
    return readiness


def validate_readiness(
    bundle: ContractBundle,
    drill_schema: Mapping[str, Any],
    readiness: Mapping[str, Any],
) -> None:
    schemas = dict(bundle.schemas)
    schemas[ROLLBACK_DRILL_SCHEMA_ID] = drill_schema
    readiness_schema = build_readiness_schema()
    schemas[READINESS_SCHEMA_ID] = readiness_schema
    try:
        registry, format_checker = build_registry(schemas)
        extended = ContractBundle(
            schemas=schemas,
            registry=registry,
            format_checker=format_checker,
            self_digest_pointers={
                **bundle.self_digest_pointers,
                ROLLBACK_DRILL_SCHEMA_ID: ROLLBACK_DRILL_SELF_POINTER,
                READINESS_SCHEMA_ID: "/artifact_digest",
            },
            policies=bundle.policies,
            protocol_revision=bundle.protocol_revision,
        )
        validate_instance(
            extended,
            readiness,
            READINESS_SCHEMA_ID,
            public=True,
        )
        scan_public_value(readiness, bundle.policies)
    except ContractError as exc:
        raise RollbackControllerBuildError(
            "ROLLBACK_CONTROLLER_READINESS_INVALID:" + str(exc)
        ) from exc


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    expected = {
        DRILL_SCHEMA_PATH: _render(build_drill_schema()),
        READINESS_SCHEMA_PATH: _render(build_readiness_schema()),
        OUTPUT_PATH: _render(build_readiness()),
    }
    if args.write:
        for path, raw in expected.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        action = "ROLLBACK_CONTROLLER_GENERATED"
    else:
        mismatches = [
            path.as_posix()
            for path, raw in expected.items()
            if not path.is_file() or path.read_bytes() != raw
        ]
        if mismatches:
            raise RollbackControllerBuildError(
                "ROLLBACK_CONTROLLER_BYTE_DRIFT:" + ",".join(mismatches)
            )
        action = "ROLLBACK_CONTROLLER_BYTE_EQUIVALENT"
    readiness = build_readiness()
    print(
        action
        + " "
        + "artifact_digest="
        + readiness["artifact_digest"]
        + " "
        + "drill_schema_sha256="
        + readiness["controller_contract"]["rollback_drill_schema"][
            "schema_sha256"
        ]
        + " real_champions=0"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RollbackControllerBuildError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
