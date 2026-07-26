#!/usr/bin/env python3
"""Build/check non-active Mechanism M-068 representative pilots."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from CodexSkills.governance.pilots.representative_pilots import (  # noqa: E402
    CANDIDATE_BUNDLE_DIGEST,
    COMMON_GATE_CODES,
    DEPENDENCY_KEYS,
    PILOT_CLASSES,
    PILOT_SCHEMA_ID,
    PILOT_SPECS,
    PROTOCOL_REVISION,
    REGISTRY_SCHEMA_ID,
    SCHEMA_PREFIX,
    SELF_POINTER,
    build_all_pilots,
    validate_pilot,
)
from CodexSkills.governance.promotion.rollback_controller import (  # noqa: E402
    REQUIRED_VERIFICATION_KINDS,
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
PILOTS_DIR = GOVERNANCE_DIR / "pilots"
SCHEMA_DIR = PILOTS_DIR / "schemas"
COMPONENT_PATH = PILOTS_DIR / "representative_pilots.py"
PILOT_SCHEMA_PATH = SCHEMA_DIR / "representative-pilot-evidence.schema.json"
READINESS_SCHEMA_PATH = (
    SCHEMA_DIR / "three-representative-pilots-readiness.schema.json"
)
READINESS_PATH = PILOTS_DIR / "three-representative-pilots-readiness.json"
PILOT_PATHS = {
    "DETERMINISTIC_SYNC": (
        PILOTS_DIR / "deterministic-sync-pilot.json"
    ),
    "SAME_NAME_MULTI_SOURCE": (
        PILOTS_DIR / "same-name-multi-source-pilot.json"
    ),
    "HIGH_RISK_ITERATIVE": (
        PILOTS_DIR / "high-risk-evolve-pilot.json"
    ),
}
VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

READINESS_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:three-representative-pilots-readiness:v1"
)
NEXT_PHASE = "MECHANISM_COLD_START_HANDOFF_RELEASE_REVIEW"
CANDIDATE_GIT_OBJECT = (
    "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5"
)
CANDIDATE_MANIFEST_PATH = (
    "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
)
CANDIDATE_MANIFEST_RAW_SHA256 = (
    "66ad125629cab71739ff2bc266219f995f7a45998936ca720c6db678ee77e65a"
)

REGISTRY_GIT_OBJECT = (
    "sha1:98e193e74991346d266bdd94ae720c32f25dfb47"
)
REGISTRY_PATH = "CodexSkills/registry/_global/registry-snapshot.v1.json"
REGISTRY_RAW_SHA256 = (
    "ed5fb74fa88a2f1115a716be5e63f683d206c10d3d0a2005230d4c33d4c12c98"
)
REGISTRY_SELF_DIGEST = (
    "7b5a74bd459a4737299444b68439c1799ba8a2159032636a24a987113eee9d12"
)

SOURCE_DOCUMENTS = {
    "failure_readiness": {
        "verified_git_object_id": (
            "sha1:6cf5beae7c50c3fb860926df670dcc5fc33890e3"
        ),
        "canonical_path": (
            "CodexSkills/governance/evaluation/"
            "failure-to-test-readiness.json"
        ),
        "content_digest": (
            "ab243507d8384a849ea9488e1a6d717c87f12195b7397300658c83d2c6e3eaf6"
        ),
        "artifact_digest": (
            "0fd20eef7a9aad02fe5301f28a3bbd91ee352dc431f9832fd372601e1425c496"
        ),
    },
    "regression_case": {
        "verified_git_object_id": (
            "sha1:6cf5beae7c50c3fb860926df670dcc5fc33890e3"
        ),
        "canonical_path": (
            "CodexSkills/governance/evaluation/"
            "confirmed-regression-case.json"
        ),
        "content_digest": (
            "006e5e770688cce4d144b8d49271c09451b7216d97da7674bf39e01cf7956bf2"
        ),
        "artifact_digest": (
            "aab2854eb272c63e2d0a1fac033f5d8aca6a371afb12e37eaf979a92028b037d"
        ),
    },
    "rollback_readiness": {
        "verified_git_object_id": (
            "sha1:6d263e02ca6104abca5ae930b5eaa0944d8d5960"
        ),
        "canonical_path": (
            "CodexSkills/governance/promotion/"
            "rollback-controller-readiness.json"
        ),
        "content_digest": (
            "9ecdbc1f5cd103d6420cdd2d81b4ab14e94ce50668c6fabfe96ba05a9fd22494"
        ),
        "artifact_digest": (
            "3cf47b465f46a458b2c16b57599462ca6638076cb32ab0e57ab2c86d6c41a93b"
        ),
    },
    "migration_readiness": {
        "verified_git_object_id": (
            "sha1:0b59768ed3697a1cd3c93afda70d96b9034f99ef"
        ),
        "canonical_path": (
            "CodexSkills/governance/migration/"
            "read-only-migration-cutover-readiness.json"
        ),
        "content_digest": (
            "839b363d904116d8657f78e10b53a1cd11c86f1d64f06064090e5a71b24ca02c"
        ),
        "artifact_digest": (
            "049809b3292f5591fc63f899c2172e67da66bb0a152998e04a341bda401d1228"
        ),
    },
}

SCHEMA_SOURCES = (
    {
        "verified_git_object_id": REGISTRY_GIT_OBJECT,
        "canonical_path": (
            "CodexSkills/governance/registry/schemas/"
            "registry-snapshot.schema.json"
        ),
        "content_digest": (
            "3b99bf37cf8380a63233849a11659842f86e1f59af4cf1d260ec4b60afe3a147"
        ),
        "schema_sha256": (
            "30684b2e024b0383f947b46aba0aab3fb3c9b4536770b365263c6e255dbc9cde"
        ),
        "self_digest_pointer": "/registry_snapshot_digest",
    },
    {
        "verified_git_object_id": SOURCE_DOCUMENTS[
            "failure_readiness"
        ]["verified_git_object_id"],
        "canonical_path": (
            "CodexSkills/governance/evaluation/schemas/"
            "confirmed-failure-incident.schema.json"
        ),
        "content_digest": (
            "7f84652a281135623ada9bea884523c343738a7d865d741b42b0282a6cf9f24e"
        ),
        "schema_sha256": (
            "4af6d1a70b1ac506f5fee46466cb02d55062928b6c3064ac3aacdec828659975"
        ),
        "self_digest_pointer": SELF_POINTER,
    },
    {
        "verified_git_object_id": SOURCE_DOCUMENTS[
            "failure_readiness"
        ]["verified_git_object_id"],
        "canonical_path": (
            "CodexSkills/governance/evaluation/schemas/"
            "confirmed-regression-case.schema.json"
        ),
        "content_digest": (
            "b7bf08c93a0fe3d994d8f62583bb404fffa0ec33cbfe1d1ba39f8a473858dd2a"
        ),
        "schema_sha256": (
            "4c0a97958901365e75b2243289a7f1d52e3352b488fb8a7ecf98748d1ffd6555"
        ),
        "self_digest_pointer": SELF_POINTER,
    },
    {
        "verified_git_object_id": SOURCE_DOCUMENTS[
            "failure_readiness"
        ]["verified_git_object_id"],
        "canonical_path": (
            "CodexSkills/governance/evaluation/schemas/"
            "failure-to-test-readiness.schema.json"
        ),
        "content_digest": (
            "1fb1c5ecada48eddb408730c53157877f32acd2c6a3109d99f0dab846f6022ce"
        ),
        "schema_sha256": (
            "9db5bc8721954e702adb63d4ed9a075f62959240261b4793a8cb2a0991d6bff9"
        ),
        "self_digest_pointer": SELF_POINTER,
    },
    {
        "verified_git_object_id": SOURCE_DOCUMENTS[
            "rollback_readiness"
        ]["verified_git_object_id"],
        "canonical_path": (
            "CodexSkills/governance/promotion/schemas/"
            "rollback-drill-evidence.schema.json"
        ),
        "content_digest": (
            "fb0741973e1889e3dc8ac73dd5f1cdcf7c8afc7a34419c669b35ae83b048f0d9"
        ),
        "schema_sha256": (
            "05ccf4edce100c3ac1502d7dec3d64418a090a9d38ff5acb04282f488ac7edea"
        ),
        "self_digest_pointer": "/evidence_bundle_digest",
    },
    {
        "verified_git_object_id": SOURCE_DOCUMENTS[
            "rollback_readiness"
        ]["verified_git_object_id"],
        "canonical_path": (
            "CodexSkills/governance/promotion/schemas/"
            "rollback-controller-readiness.schema.json"
        ),
        "content_digest": (
            "ef95d965462bf67ee1af9d75951b3e41d1d47856ee206e63bc539e940eb3bb43"
        ),
        "schema_sha256": (
            "e945d9df234aba24f38141000f5b26570862c275bf4c063c9ba216de18ea978c"
        ),
        "self_digest_pointer": SELF_POINTER,
    },
    {
        "verified_git_object_id": SOURCE_DOCUMENTS[
            "migration_readiness"
        ]["verified_git_object_id"],
        "canonical_path": (
            "CodexSkills/governance/migration/schemas/"
            "read-only-migration-observation.schema.json"
        ),
        "content_digest": (
            "7507b62535395f52a8037ff5168c1b1e3019d04635b6a7015704c3b2bad8e304"
        ),
        "schema_sha256": (
            "6d769bd378ee2526155fbfab29de89ec7754b41c026104a989a164a980505a97"
        ),
        "self_digest_pointer": "/evidence_bundle_digest",
    },
    {
        "verified_git_object_id": SOURCE_DOCUMENTS[
            "migration_readiness"
        ]["verified_git_object_id"],
        "canonical_path": (
            "CodexSkills/governance/migration/schemas/"
            "read-only-cutover-plan.schema.json"
        ),
        "content_digest": (
            "bbdba195fd3f40c47d31694d239b65d282b51cb8604f511014bfbc8732e55792"
        ),
        "schema_sha256": (
            "f800865090ce43f86ab78d69f306592a801f40faaad3bc2a167f20ecb3209d39"
        ),
        "self_digest_pointer": "/evidence_bundle_digest",
    },
    {
        "verified_git_object_id": SOURCE_DOCUMENTS[
            "migration_readiness"
        ]["verified_git_object_id"],
        "canonical_path": (
            "CodexSkills/governance/migration/schemas/"
            "read-only-migration-cutover-readiness.schema.json"
        ),
        "content_digest": (
            "2ceaa60ec6e8ecc52d1ddb5d83e4ccc48fadcd5f0481f8286839262df7feb619"
        ),
        "schema_sha256": (
            "d63de0996742f8943f905827b4eeb35ba0137b09b10acd3a84e45460ba717e9e"
        ),
        "self_digest_pointer": SELF_POINTER,
    },
)

REF = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:common-definitions:v1#/$defs/"
)


class RepresentativePilotBuildError(ValueError):
    """M-068 evidence cannot be rebuilt without weakening a gate."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _render(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _load(raw: bytes, code: str) -> Mapping[str, Any]:
    try:
        value = parse_json_bytes(raw)
    except Exception as exc:
        raise RepresentativePilotBuildError(code) from exc
    if not isinstance(value, dict):
        raise RepresentativePilotBuildError(code)
    return value


def _git_blob(tagged_object: str, relative_path: str) -> bytes:
    if tagged_object.count(":") != 1:
        raise RepresentativePilotBuildError("M068_GIT_OBJECT_INVALID")
    algorithm, object_id = tagged_object.split(":", 1)
    if algorithm != "sha1" or len(object_id) != 40:
        raise RepresentativePilotBuildError("M068_GIT_OBJECT_INVALID")
    process = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", object_id + ":" + relative_path],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    if process.returncode != 0:
        raise RepresentativePilotBuildError(
            "M068_GIT_BLOB_UNAVAILABLE:" + relative_path
        )
    return process.stdout


def _current(relative_path: str) -> bytes:
    path = REPO_ROOT.joinpath(*relative_path.split("/"))
    if not path.is_file() or path.is_symlink():
        raise RepresentativePilotBuildError(
            "M068_CURRENT_FILE_INVALID:" + relative_path
        )
    return path.read_bytes()


def _ref(name: str) -> Mapping[str, str]:
    return {"$ref": REF + name}


def _closed(
    properties: Mapping[str, Any],
    required: Optional[Sequence[str]] = None,
) -> Mapping[str, Any]:
    return {
        "additionalProperties": False,
        "properties": dict(properties),
        "required": list(required or properties),
        "type": "object",
    }


def _digest_array(*, min_items: int = 1) -> Mapping[str, Any]:
    return {
        "items": _ref("sha256"),
        "minItems": min_items,
        "type": "array",
        "uniqueItems": True,
    }


def build_pilot_schema() -> Mapping[str, Any]:
    digest_ref = _closed({"artifact_digest": _ref("sha256")})
    version_ref = _closed({"version_record_digest": _ref("sha256")})
    member = _closed(
        {
            "source_class": _ref("source_class"),
            "source_relative_path": _ref("repo_relative_posix_path"),
            "skill_identity_uid": _ref("skill_identity_uid"),
            "identity_ref": digest_ref,
            "skill_instance_uid": _ref("skill_instance_uid"),
            "instance_ref": digest_ref,
            "skill_version_uid": _ref("skill_version_uid"),
            "version_ref": version_ref,
            "source_fingerprint_digest": _ref("sha256"),
            "content_digest": _ref("sha256"),
            "lifecycle_status": {"const": "QUARANTINED"},
            "trust_tier": {"const": "UNVERIFIED"},
            "binding_eligible": {"const": False},
            "eval_profile_present": {"const": False},
            "permissions_resolved": {"const": False},
        }
    )
    identity_resolution = _closed(
        {
            "registry_identity_uids": {
                "items": _ref("skill_identity_uid"),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "selected_identity_uids": {
                "items": _ref("skill_identity_uid"),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "registry_identity_count": _ref("positive_count"),
            "selected_identity_count": _ref("positive_count"),
            "same_name_auto_merge_permitted": {"const": False},
            "owner_review_required": {"type": "boolean"},
        }
    )
    gate = _closed(
        {
            "gate_code": {"type": "string"},
            "critical": {"const": True},
            "status": {"const": "PASS"},
            "evidence_digests": _digest_array(),
        }
    )
    verification = _closed(
        {
            "kind": {
                "enum": list(REQUIRED_VERIFICATION_KINDS)
            },
            "artifact_digest": _ref("sha256"),
        }
    )
    drill = _closed(
        {
            "status": {"const": "SHADOW_PASS"},
            "mode": {"const": "SYNTHETIC_PRE_WRITE_NO_STATE"},
            "verification_evidence_refs": {
                "items": verification,
                "maxItems": len(REQUIRED_VERIFICATION_KINDS),
                "minItems": len(REQUIRED_VERIFICATION_KINDS),
                "type": "array",
            },
            "synthetic_prior_champion_restorable": {"const": True},
            "real_registry_champion_present": {"const": False},
            "history_rewrite_performed": {"const": False},
            "state_write_observed": {"const": False},
            "notification_sent": {"const": False},
            "production_drill": {"const": False},
            "evidence_bundle_digest": _ref("sha256"),
        }
    )
    cycle = _closed(
        {
            "cycle_index": {
                "maximum": 3,
                "minimum": 1,
                "type": "integer",
            },
            "mode": {
                "const": "DETERMINISTIC_SHADOW_METADATA_ONLY"
            },
            "member_version_uids": {
                "items": _ref("skill_version_uid"),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "shadow_evidence_digest": _ref("sha256"),
            "gate_results": {
                "items": gate,
                "minItems": len(COMMON_GATE_CODES) + 1,
                "type": "array",
            },
            "rollback_drill": drill,
            "side_effect_count": {"const": 0},
            "registry_write_count": {"const": 0},
            "state_write_count": {"const": 0},
            "notification_count": {"const": 0},
            "publication_count": {"const": 0},
            "evidence_digest": _ref("sha256"),
        }
    )
    summary = _closed(
        {
            "cycle_count": {"const": 3},
            "clean_cycle_count": {"const": 3},
            "all_shadow_critical_gates_passed": {"const": True},
            "all_shadow_rollback_drills_passed": {"const": True},
            "three_cycle_result_stable": {"const": True},
            "production_critical_gates_passed": {"const": False},
            "production_pilot_executed": {"const": False},
            "production_blocker_codes": {
                "items": {"type": "string"},
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
        }
    )
    return {
        "$id": PILOT_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **_closed(
            {
                "schema_version": {"const": PILOT_SCHEMA_ID},
                "protocol_revision": _ref("protocol_revision"),
                "bundle_digest": _ref("sha256"),
                "pilot_uid": _ref("typed_uid"),
                "pilot_class": {"enum": list(PILOT_CLASSES)},
                "canonical_name": {
                    "maxLength": 128,
                    "minLength": 1,
                    "type": "string",
                },
                "execution_mode": {
                    "const": "DETERMINISTIC_SHADOW_METADATA_ONLY"
                },
                "status": {
                    "const": "SHADOW_COMPLETE_PRODUCTION_BLOCKED"
                },
                "registry_snapshot_digest": _ref("sha256"),
                "members": {
                    "items": member,
                    "maxItems": 2,
                    "minItems": 1,
                    "type": "array",
                },
                "identity_resolution": identity_resolution,
                "cycles": {
                    "items": cycle,
                    "maxItems": 3,
                    "minItems": 3,
                    "type": "array",
                },
                "summary": summary,
                "artifact_digest": _ref("sha256"),
            }
        ),
        "title": "Mechanism M-068 representative Shadow pilot evidence",
    }


def _source_material() -> Tuple[
    Mapping[str, Any],
    Mapping[str, Mapping[str, Any]],
    Mapping[str, Mapping[str, Any]],
    Mapping[str, str],
]:
    registry_raw = _git_blob(REGISTRY_GIT_OBJECT, REGISTRY_PATH)
    if (
        _sha256(registry_raw) != REGISTRY_RAW_SHA256
        or _current(REGISTRY_PATH) != registry_raw
    ):
        raise RepresentativePilotBuildError("M068_REGISTRY_RAW_DRIFT")
    snapshot = _load(registry_raw, "M068_REGISTRY_JSON_INVALID")
    if (
        snapshot.get("registry_snapshot_digest")
        != REGISTRY_SELF_DIGEST
        or canonical_digest(snapshot, "/registry_snapshot_digest")
        != REGISTRY_SELF_DIGEST
    ):
        raise RepresentativePilotBuildError(
            "M068_REGISTRY_SELF_DIGEST_MISMATCH"
        )

    dependencies = {}
    for key in DEPENDENCY_KEYS:
        contract = SOURCE_DOCUMENTS[key]
        raw = _git_blob(
            contract["verified_git_object_id"],
            contract["canonical_path"],
        )
        if (
            _sha256(raw) != contract["content_digest"]
            or _current(contract["canonical_path"]) != raw
        ):
            raise RepresentativePilotBuildError(
                "M068_DEPENDENCY_RAW_DRIFT:" + key
            )
        value = _load(raw, "M068_DEPENDENCY_JSON_INVALID:" + key)
        if (
            value.get("artifact_digest")
            != contract["artifact_digest"]
            or canonical_digest(value, SELF_POINTER)
            != contract["artifact_digest"]
        ):
            raise RepresentativePilotBuildError(
                "M068_DEPENDENCY_SELF_DIGEST_MISMATCH:" + key
            )
        dependencies[key] = value

    schemas = {}
    pointers = {}
    for contract in SCHEMA_SOURCES:
        raw = _git_blob(
            contract["verified_git_object_id"],
            contract["canonical_path"],
        )
        if (
            _sha256(raw) != contract["content_digest"]
            or _current(contract["canonical_path"]) != raw
        ):
            raise RepresentativePilotBuildError(
                "M068_SCHEMA_RAW_DRIFT:" + contract["canonical_path"]
            )
        schema = _load(raw, "M068_SCHEMA_JSON_INVALID")
        if canonical_digest(schema) != contract["schema_sha256"]:
            raise RepresentativePilotBuildError(
                "M068_SCHEMA_DIGEST_MISMATCH:" + schema.get("$id", "")
            )
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or schema_id in schemas:
            raise RepresentativePilotBuildError(
                "M068_SCHEMA_ID_INVALID_OR_DUPLICATE"
            )
        schemas[schema_id] = schema
        pointers[schema_id] = contract["self_digest_pointer"]
    if REGISTRY_SCHEMA_ID not in schemas or len(schemas) != 9:
        raise RepresentativePilotBuildError(
            "M068_EXTERNAL_SCHEMA_SET_INVALID"
        )
    return snapshot, dependencies, schemas, pointers


def _extend_bundle(
    base: ContractBundle,
    additions: Mapping[str, Mapping[str, Any]],
    pointers: Mapping[str, str],
) -> ContractBundle:
    schemas = dict(base.schemas)
    self_pointers = dict(base.self_digest_pointers)
    for schema_id, schema in additions.items():
        if schema_id in schemas:
            raise RepresentativePilotBuildError(
                "M068_SCHEMA_REBIND_FORBIDDEN:" + schema_id
            )
        schemas[schema_id] = schema
        self_pointers[schema_id] = pointers[schema_id]
    try:
        registry, checker = build_registry(schemas)
    except ContractError as exc:
        raise RepresentativePilotBuildError(
            "M068_SCHEMA_CLOSURE_INVALID:" + str(exc)
        ) from exc
    return ContractBundle(
        schemas=schemas,
        registry=registry,
        format_checker=checker,
        self_digest_pointers=self_pointers,
        policies=base.policies,
        protocol_revision=base.protocol_revision,
    )


def _descriptor(
    schema_id: str,
    path: Path,
    raw: bytes,
    schema: Mapping[str, Any],
) -> Mapping[str, Any]:
    return {
        "schema_version": schema_id,
        "canonical_path": path.relative_to(REPO_ROOT).as_posix(),
        "content_digest": _sha256(raw),
        "schema_sha256": canonical_digest(schema),
        "self_digest_pointer": SELF_POINTER,
    }


def _build_readiness(
    pilots: Sequence[Mapping[str, Any]],
    pilot_schema: Mapping[str, Any],
) -> Mapping[str, Any]:
    pilot_schema_raw = _render(pilot_schema)
    blockers = sorted(
        {
            code
            for pilot in pilots
            for code in pilot["summary"]["production_blocker_codes"]
        }
    )
    pilot_outputs = []
    for pilot in pilots:
        path = PILOT_PATHS[pilot["pilot_class"]]
        raw = _render(pilot)
        pilot_outputs.append(
            {
                "pilot_class": pilot["pilot_class"],
                "canonical_name": pilot["canonical_name"],
                "canonical_path": path.relative_to(REPO_ROOT).as_posix(),
                "content_digest": _sha256(raw),
                "artifact_digest": pilot["artifact_digest"],
                "cycle_count": 3,
                "clean_cycle_count": 3,
                "shadow_rollback_drill_count": 3,
                "production_pilot_executed": False,
            }
        )
    value: Dict[str, Any] = {
        "schema_version": READINESS_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        "status": (
            "DRAFT_NON_ACTIVE_THREE_REPRESENTATIVE_PILOTS_"
            "SHADOW_COMPLETE_PRODUCTION_BLOCKED"
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
            "registry_snapshot": {
                "verified_git_object_id": REGISTRY_GIT_OBJECT,
                "canonical_path": REGISTRY_PATH,
                "content_digest": REGISTRY_RAW_SHA256,
                "registry_snapshot_digest": REGISTRY_SELF_DIGEST,
                "expected_mode": "REGISTERED_READ_ONLY",
                "identity_count": 89,
                "instance_count": 89,
                "version_count": 89,
                "binding_eligible_version_count": 0,
            },
            "dependency_sources": [
                {"dependency_code": key.upper(), **SOURCE_DOCUMENTS[key]}
                for key in DEPENDENCY_KEYS
            ],
            "repository_self_report_is_not_trust_root": True,
        },
        "implementation_contract": {
            "component_path": (
                "CodexSkills/governance/pilots/"
                "representative_pilots.py"
            ),
            "content_digest": _sha256(COMPONENT_PATH.read_bytes()),
            "capability_mode": "PURE_IMMUTABLE_OBJECTS_ONLY",
            "pilot_schema": _descriptor(
                PILOT_SCHEMA_ID,
                PILOT_SCHEMA_PATH,
                pilot_schema_raw,
                pilot_schema,
            ),
            "pilot_outputs": pilot_outputs,
            "pilot_class_order": list(PILOT_CLASSES),
            "required_cycle_count_per_pilot": 3,
            "required_rollback_verification_kinds": list(
                REQUIRED_VERIFICATION_KINDS
            ),
            "caller_gate_or_status_fields_accepted": False,
            "skill_execution_capability_present": False,
            "source_content_read_capability_present": False,
            "sealed_holdout_read_capability_present": False,
            "filesystem_capability_present": False,
            "git_capability_present": False,
            "network_capability_present": False,
            "state_capability_present": False,
            "publisher_capability_present": False,
        },
        "current_summary": {
            "pilot_count": len(pilots),
            "cycle_count": sum(
                pilot["summary"]["cycle_count"] for pilot in pilots
            ),
            "clean_cycle_count": sum(
                pilot["summary"]["clean_cycle_count"]
                for pilot in pilots
            ),
            "shadow_rollback_drill_count": sum(
                len(pilot["cycles"]) for pilot in pilots
            ),
            "all_shadow_critical_gates_passed": all(
                pilot["summary"][
                    "all_shadow_critical_gates_passed"
                ]
                for pilot in pilots
            ),
            "all_shadow_rollback_drills_passed": all(
                pilot["summary"][
                    "all_shadow_rollback_drills_passed"
                ]
                for pilot in pilots
            ),
            "all_three_cycle_results_stable": all(
                pilot["summary"]["three_cycle_result_stable"]
                for pilot in pilots
            ),
            "same_name_auto_merge_performed": False,
            "real_skill_execution_performed": False,
            "real_rollback_execution_performed": False,
            "real_notification_sent": False,
            "production_critical_gates_passed": False,
            "production_pilots_ready": False,
            "production_blocker_codes": blockers,
        },
        "nonmutation": {
            "auto_plane_unchanged": True,
            "openai_database_unchanged": True,
            "candidate_bundle_unchanged": True,
            "registry_write_permitted": False,
            "source_write_permitted": False,
            "evaluation_profile_mutated": False,
            "real_skill_executed": False,
            "real_rollback_executed": False,
            "notification_sent": False,
            "state_write_permitted": False,
            "watermark_advance_permitted": False,
            "canonical_publication_permitted": False,
            "migration_cutover_permitted": False,
            "activation_forbidden": True,
            "version_file_created": False,
        },
        "task_contract": {
            "dependency_task_ids": ["M-046", "M-057", "M-065"],
            "implemented_task_ids": ["M-068"],
            "pending_task_ids": ["M-069"],
            "required_output_code": (
                "SYNC_DUPLICATE_IDENTITY_HIGH_RISK_EVOLVE_EVIDENCE"
            ),
            "done_gate": (
                "ALL_CRITICAL_GATES_AND_ROLLBACK_DRILLS_PASS"
            ),
            "done_gate_scope": "DETERMINISTIC_SHADOW_ONLY",
            "production_done_gate_satisfied": False,
        },
        "schema_closure_count": 42,
        "policy_count": 5,
        "production_pilots_ready": False,
        "next_phase": NEXT_PHASE,
        "self_digest_pointer": SELF_POINTER,
        "task_pack_revision": "v0.0.0.2",
        "artifact_digest": "0" * 64,
    }
    value["artifact_digest"] = canonical_digest(value, SELF_POINTER)
    return value


def build_readiness_schema(
    readiness: Mapping[str, Any],
) -> Mapping[str, Any]:
    properties = {
        key: {"const": value}
        for key, value in readiness.items()
        if key != "artifact_digest"
    }
    properties["artifact_digest"] = _ref("sha256")
    return {
        "$id": READINESS_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **_closed(properties),
        "title": "Mechanism M-068 representative pilots readiness",
    }


def _documents() -> Mapping[Path, bytes]:
    snapshot, dependencies, external_schemas, external_pointers = (
        _source_material()
    )
    pilots = build_all_pilots(snapshot, dependencies)
    for pilot in pilots:
        validate_pilot(pilot, snapshot, dependencies)
    pilot_schema = build_pilot_schema()
    base = _extend_bundle(
        load_au040_acceptance().bundle,
        external_schemas,
        external_pointers,
    )
    readiness = _build_readiness(pilots, pilot_schema)
    readiness_schema = build_readiness_schema(readiness)
    contract = _extend_bundle(
        base,
        {
            PILOT_SCHEMA_ID: pilot_schema,
            READINESS_SCHEMA_ID: readiness_schema,
        },
        {
            PILOT_SCHEMA_ID: SELF_POINTER,
            READINESS_SCHEMA_ID: SELF_POINTER,
        },
    )
    if len(contract.schemas) != 42 or len(contract.policies) != 5:
        raise RepresentativePilotBuildError(
            "M068_SCHEMA_OR_POLICY_COUNT_INVALID"
        )
    validate_instance(
        contract,
        snapshot,
        REGISTRY_SCHEMA_ID,
        expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
        verify_digest=True,
        public=True,
    )
    dependency_schema_ids = {
        "failure_readiness": (
            SCHEMA_PREFIX + "failure-to-test-readiness:v1"
        ),
        "regression_case": (
            SCHEMA_PREFIX + "confirmed-regression-case:v1"
        ),
        "rollback_readiness": (
            SCHEMA_PREFIX + "rollback-controller-readiness:v1"
        ),
        "migration_readiness": (
            SCHEMA_PREFIX
            + "read-only-migration-cutover-readiness:v1"
        ),
    }
    for key in DEPENDENCY_KEYS:
        validate_instance(
            contract,
            dependencies[key],
            dependency_schema_ids[key],
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            verify_digest=True,
            public=True,
        )
    for pilot in pilots:
        validate_instance(
            contract,
            pilot,
            PILOT_SCHEMA_ID,
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            verify_digest=True,
            public=True,
        )
        scan_public_value(pilot, contract.policies)
    validate_instance(
        contract,
        readiness,
        READINESS_SCHEMA_ID,
        expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
        verify_digest=True,
        public=True,
    )
    scan_public_value(readiness, contract.policies)
    documents: Dict[Path, bytes] = {
        PILOT_SCHEMA_PATH: _render(pilot_schema),
        READINESS_SCHEMA_PATH: _render(readiness_schema),
        READINESS_PATH: _render(readiness),
    }
    for pilot in pilots:
        documents[PILOT_PATHS[pilot["pilot_class"]]] = _render(pilot)
    return documents


def _write() -> None:
    for path, raw in _documents().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def _check() -> None:
    for path, expected in _documents().items():
        if not path.is_file() or path.is_symlink():
            raise RepresentativePilotBuildError(
                "M068_GENERATED_FILE_INVALID:" + str(path)
            )
        if path.read_bytes() != expected:
            raise RepresentativePilotBuildError(
                "M068_GENERATED_BYTE_DRIFT:" + str(path)
            )
    if VERSION_PATH.exists():
        raise RepresentativePilotBuildError(
            "M068_VERSION_MUST_REMAIN_ABSENT"
        )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write:
            _write()
        else:
            _check()
        readiness = _load(
            _documents()[READINESS_PATH],
            "M068_READINESS_INVALID",
        )
        summary = readiness["current_summary"]
        print(
            "REPRESENTATIVE_PILOTS_OK pilots="
            + str(summary["pilot_count"])
            + " cycles="
            + str(summary["cycle_count"])
            + " shadow_rollbacks="
            + str(summary["shadow_rollback_drill_count"])
            + " shadow_pass=true production_ready=false"
        )
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
