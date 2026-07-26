#!/usr/bin/env python3
"""Build/check non-active Mechanism M-059 protection evidence."""

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

from CodexSkills.governance.monitoring.freshness_drift import (  # noqa: E402
    build_monitor_contract,
)
from CodexSkills.governance.promotion.controller import (  # noqa: E402
    PROTOCOL_REVISION,
    build_registry_view,
)
from CodexSkills.governance.release.policy_protection import (  # noqa: E402
    AUDIT_REQUIREMENTS,
    EVAL_PROFILE_SCHEMA_ID,
    OBSERVATION_SCHEMA_ID,
    OBSERVATION_SELF_POINTER,
    POLICY_CODES,
    REPORT_SCHEMA_ID,
    REPORT_SELF_POINTER,
    build_protection_contract,
)
from CodexSkills.governance.release.version_policy_v3.contract import (  # noqa: E402
    VERSION_POLICY_V3_ID,
    validate_version_policy_v3,
)
from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_mechanism import (  # noqa: E402
    ContractBundle,
    TrustTuple,
    load_trusted_bundle,
    scan_public_value,
    validate_instance,
)


GOVERNANCE_DIR = REPO_ROOT / "CodexSkills" / "governance"
RELEASE_DIR = GOVERNANCE_DIR / "release"
OUTPUT_PATH = RELEASE_DIR / "evaluator-release-protection-readiness.json"
OBSERVATION_SCHEMA_PATH = (
    RELEASE_DIR
    / "schemas"
    / "evaluator-release-change-observation.schema.json"
)
REPORT_SCHEMA_PATH = (
    RELEASE_DIR
    / "schemas"
    / "evaluator-release-protection-report.schema.json"
)
READINESS_SCHEMA_PATH = (
    RELEASE_DIR
    / "schemas"
    / "evaluator-release-protection-readiness.schema.json"
)
PROTECTION_PATH = RELEASE_DIR / "policy_protection.py"
REGISTRY_SNAPSHOT_PATH = (
    REPO_ROOT
    / "CodexSkills"
    / "registry"
    / "_global"
    / "registry-snapshot.v1.json"
)
VERSION_POLICY_PATH = (
    RELEASE_DIR / "version_policy_v3" / "version-policy.v3.json"
)
VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

READINESS_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:evaluator-release-protection-readiness:v1"
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
M056_CONTROLLER_PATH = "CodexSkills/governance/promotion/controller.py"
M056_CONTROLLER_RAW_SHA256 = (
    "bcc39aaa1e6c817fb321a8772996a05fffffe947cd8bbc218a5f7bad16db3e53"
)
M056_READINESS_PATH = (
    "CodexSkills/governance/promotion/controller-readiness.json"
)
M056_READINESS_RAW_SHA256 = (
    "d54d577bf53e155c1eb6215db388d9f7939f91e21d6af938242c49928b44d1ae"
)
M058_GIT_OBJECT = (
    "sha1:3d3c202ee629d79eadfb027da131e1afcb88a1f2"
)
M058_MONITOR_PATH = (
    "CodexSkills/governance/monitoring/freshness_drift.py"
)
M058_MONITOR_RAW_SHA256 = (
    "ef703ede2b18c91f907ab6e9db1fedb2923b5fc2a9d456becae4b27a087af1a3"
)
M058_READINESS_PATH = (
    "CodexSkills/governance/monitoring/freshness-drift-readiness.json"
)
M058_READINESS_RAW_SHA256 = (
    "416beacd6a72d3d5517211a3758452228bd445ab10fc887928b0575e2865d812"
)
M058_OBSERVATION_SCHEMA_PATH = (
    "CodexSkills/governance/monitoring/schemas/"
    "freshness-drift-observation.schema.json"
)
M058_OBSERVATION_SCHEMA_SHA256 = (
    "ebda03e6ad49a2fef25b14f5b587bdddbed1075f6fc3fe175b16366b227fca50"
)
M058_REPORT_SCHEMA_PATH = (
    "CodexSkills/governance/monitoring/schemas/"
    "freshness-drift-report.schema.json"
)
M058_REPORT_SCHEMA_SHA256 = (
    "2b529885458798f070d089bdee8e3fbfa032072a3f74c0c43c8de236c7e57581"
)
VERSION_POLICY_GIT_OBJECT = (
    "sha1:07f7925185f7e1486f808042a10c383ba52d572f"
)
VERSION_POLICY_INTERFACE_PATH = (
    "CodexSkills/governance/release/version_policy_v3/draft-interface.json"
)
VERSION_POLICY_INTERFACE_RAW_SHA256 = (
    "0fa8303981a1b263c835e74cc864fb114c4e1d4eb1a5e8c317c140754b84b8f7"
)
VERSION_POLICY_REPO_PATH = (
    "CodexSkills/governance/release/version_policy_v3/version-policy.v3.json"
)
VERSION_POLICY_SHA256 = (
    "5ea6047446ef26ab39d0e284f37619859d57c8c419daa1cffefffdc12935cfe0"
)
NEXT_PHASE = "MECHANISM_PROTECTED_LOCAL_DATA_MANAGED_RAW_BOUNDARY"

CHANGE_CODES = (
    "EVALUATION_DATA_CHANGE",
    "EVALUATION_POLICY_CHANGE",
    "EVALUATOR_MANIFEST_CHANGE",
    "EVAL_PROFILE_RECORD_CHANGE",
    "EVAL_PROFILE_SET_CHANGE",
    "HARD_GATE_SET_CHANGE",
    "JUDGE_CALIBRATION_CHANGE",
    "JUDGE_RUBRIC_CHANGE",
    "JUDGE_WEIGHT_CHANGE",
    "PROMOTION_CONTROLLER_CHANGE",
    "RELEASE_NOTIFICATION_POLICY_CHANGE",
    "RELEASE_POLICY_SNAPSHOT_CHANGE",
    "RELEASE_PRIVACY_POLICY_CHANGE",
    "RELEASE_RETENTION_POLICY_CHANGE",
    "RELEASE_SOURCE_POLICY_CHANGE",
    "RELEASE_VERSION_POLICY_CHANGE",
    "SEALED_HOLDOUT_CHANGE",
)
MAJOR_TRIGGER_CODES = (
    "EVALUATOR_OR_HOLDOUT_CHANGE",
    "HARD_GATE_CHANGE",
    "NOTIFICATION_POLICY_CHANGE",
    "PRIVACY_POLICY_CHANGE",
    "RETENTION_POLICY_CHANGE",
    "SOURCE_LAYOUT_CHANGE",
)


class EvaluatorReleaseProtectionBuildError(ValueError):
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
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_JSON_INVALID:" + path.as_posix()
        ) from exc
    if not isinstance(value, dict):
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_JSON_ROOT_INVALID:" + path.as_posix()
        )
    return value


def _git_blob(tagged_object: str, relative_path: str) -> bytes:
    if tagged_object.count(":") != 1:
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_GIT_OBJECT_INVALID"
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
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_GIT_UNAVAILABLE"
        ) from exc
    if process.returncode != 0:
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_GIT_BLOB_UNAVAILABLE:" + relative_path
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


def _profile_ref() -> Dict[str, Any]:
    return _closed(
        {
            "skill_identity_uid": _ref("skill_identity_uid"),
            "eval_profile_uid": _ref("eval_profile_uid"),
            "artifact_digest": _ref("sha256"),
        }
    )


def _release_snapshot() -> Dict[str, Any]:
    policy_descriptor = _closed(
        {
            "policy_code": {"enum": list(POLICY_CODES)},
            "policy_id": _ref("urn_id"),
            "policy_sha256": _ref("sha256"),
        }
    )
    return _closed(
        {
            "policy_snapshot_digest": _ref("sha256"),
            "policy_descriptors": {
                "items": policy_descriptor,
                "maxItems": len(POLICY_CODES),
                "minItems": len(POLICY_CODES),
                "type": "array",
            },
            "promotion_controller": _closed(
                {
                    "canonical_path": _ref(
                        "repo_relative_posix_path"
                    ),
                    "artifact_digest": _ref("sha256"),
                }
            ),
        }
    )


def build_observation_schema() -> Mapping[str, Any]:
    attempt = _closed(
        {
            "attempt_code": {
                "enum": [row[0] for row in AUDIT_REQUIREMENTS]
            },
            "resource_code": {
                "enum": sorted({row[1] for row in AUDIT_REQUIREMENTS})
            },
            "operation": {"enum": ["READ", "WRITE"]},
            "outcome": {"const": "DENIED"},
            "evidence_digest": _ref("sha256"),
        }
    )
    audit = _closed(
        {
            "audit_uid": _ref("typed_uid"),
            "optimizer_actor_ref": _ref("enum_code"),
            "evaluator_actor_ref": _ref("enum_code"),
            "release_actor_ref": _ref("enum_code"),
            "roles_distinct": {"const": True},
            "attempts": {
                "items": attempt,
                "maxItems": len(AUDIT_REQUIREMENTS),
                "minItems": len(AUDIT_REQUIREMENTS),
                "type": "array",
            },
            "forbidden_attempt_count": {
                "const": len(AUDIT_REQUIREMENTS)
            },
            "denied_attempt_count": {
                "const": len(AUDIT_REQUIREMENTS)
            },
            "allowed_forbidden_attempt_count": {"const": 0},
            "completed_at": _ref("utc_z_timestamp"),
        }
    )
    properties = {
        "schema_version": {"const": OBSERVATION_SCHEMA_ID},
        "protocol_revision": _ref("protocol_revision"),
        "bundle_digest": _ref("sha256"),
        "observation_uid": _ref("typed_uid"),
        "promotion_decision_ref": _closed(
            {"decision_digest": _ref("sha256")}
        ),
        "promotion_evidence_ref": _closed(
            {"artifact_digest": _ref("sha256")}
        ),
        "baseline_eval_profiles": {
            "items": {"$ref": EVAL_PROFILE_SCHEMA_ID},
            "minItems": 1,
            "type": "array",
        },
        "proposed_eval_profiles": {
            "items": {"$ref": EVAL_PROFILE_SCHEMA_ID},
            "minItems": 1,
            "type": "array",
        },
        "baseline_release_snapshot": _release_snapshot(),
        "proposed_release_snapshot": _release_snapshot(),
        "change_origin": _closed(
            {
                "source_role": {
                    "enum": [
                        "INDEPENDENT_EVALUATOR",
                        "OPTIMIZER",
                        "RELEASE_AUTHORIZER",
                    ]
                },
                "actor_ref": _ref("enum_code"),
            }
        ),
        "isolation_audit": audit,
        "optimizer_evaluator_isolation_digest": _ref("sha256"),
        "observed_at": _ref("utc_z_timestamp"),
        "actor": {"const": "SKILLOPS_EVALUATOR_RELEASE_GUARD"},
        "evidence_bundle_digest": _ref("sha256"),
    }
    return {
        "$id": OBSERVATION_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
        "title": "Evaluator and release-policy change observation",
        "type": "object",
    }


def build_report_schema() -> Mapping[str, Any]:
    change = _closed(
        {
            "change_code": {"enum": list(CHANGE_CODES)},
            "major_trigger_code": {
                "enum": list(MAJOR_TRIGGER_CODES)
            },
            "subject_codes": {
                "items": _ref("enum_code"),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "evidence_digest": _ref("sha256"),
        }
    )
    properties = {
        "schema_version": {"const": REPORT_SCHEMA_ID},
        "protocol_revision": _ref("protocol_revision"),
        "bundle_digest": _ref("sha256"),
        "report_uid": _ref("typed_uid"),
        "promotion_decision_ref": _closed(
            {"decision_digest": _ref("sha256")}
        ),
        "promotion_evidence_ref": _closed(
            {"artifact_digest": _ref("sha256")}
        ),
        "observation_ref": _closed(
            {"artifact_digest": _ref("sha256")}
        ),
        "baseline_eval_profile_refs": {
            "items": _profile_ref(),
            "minItems": 1,
            "type": "array",
        },
        "proposed_eval_profile_refs": {
            "items": _profile_ref(),
            "minItems": 1,
            "type": "array",
        },
        "detected_changes": {
            "items": change,
            "type": "array",
        },
        "major_trigger_codes": {
            "items": {"enum": list(MAJOR_TRIGGER_CODES)},
            "type": "array",
            "uniqueItems": True,
        },
        "impact": {"enum": ["MAJOR", "NONE"]},
        "classification": _closed(
            {
                "policy_id": {"const": VERSION_POLICY_V3_ID},
                "policy_sha256": _ref("sha256"),
                "impact_downgrade_allowed": {"const": False},
                "unknown_trigger_action": {"const": "FAIL_CLOSED"},
            }
        ),
        "isolation_gate": _closed(
            {
                "status": {"const": "PASS"},
                "optimizer_evaluator_isolation_digest": _ref(
                    "sha256"
                ),
                "roles_distinct": {"const": True},
                "forbidden_attempt_count": {
                    "const": len(AUDIT_REQUIREMENTS)
                },
                "denied_attempt_count": {
                    "const": len(AUDIT_REQUIREMENTS)
                },
                "all_forbidden_attempts_denied": {"const": True},
            }
        ),
        "promotion_gate": _closed(
            {
                "status": {"enum": ["BLOCKED", "PASS"]},
                "reason_code": {
                    "enum": [
                        "INDEPENDENT_MAJOR_RELEASE_REQUIRED",
                        "OPTIMIZER_PROTECTED_CHANGE_BLOCKED",
                        "PROTECTED_SURFACES_UNCHANGED",
                    ]
                },
                "optimizer_self_improvement_permitted": {
                    "const": False
                },
                "protected_release_write_permitted": {"const": False},
                "separate_major_release_required": {
                    "type": "boolean"
                },
                "m058_delegation_permitted": {"type": "boolean"},
            }
        ),
        "generated_at": _ref("utc_z_timestamp"),
        "actor": {"const": "SKILLOPS_EVALUATOR_RELEASE_GUARD"},
        "evidence_bundle_digest": _ref("sha256"),
    }
    return {
        "$id": REPORT_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
        "title": "Evaluator and release-policy protection report",
        "type": "object",
    }


def _schema_descriptor(
    *,
    path: str,
    schema_id: str,
    schema: Mapping[str, Any],
    pointer: str,
) -> Dict[str, Any]:
    return {
        "artifact_digest": _sha256(_render(schema)),
        "canonical_path": path,
        "schema_sha256": canonical_digest(schema),
        "schema_version": schema_id,
        "self_digest_pointer": pointer,
    }


def _trust_descriptor(
    *,
    artifact_digest: str,
    canonical_path: str,
    expected_mode: str,
    verified_git_object_id: str,
) -> Dict[str, Any]:
    return {
        "artifact_digest": artifact_digest,
        "canonical_path": canonical_path,
        "expected_mode": expected_mode,
        "verified_git_object_id": verified_git_object_id,
    }


def build_readiness_schema() -> Mapping[str, Any]:
    trust = _closed(
        {
            "artifact_digest": _ref("sha256"),
            "canonical_path": _ref("repo_relative_posix_path"),
            "expected_mode": _ref("enum_code"),
            "verified_git_object_id": _ref("git_object_id"),
        }
    )
    predecessor = _closed(
        {
            **trust["properties"],
            "readiness_artifact": _closed(
                {
                    "artifact_digest": _ref("sha256"),
                    "canonical_path": _ref(
                        "repo_relative_posix_path"
                    ),
                }
            ),
        }
    )
    candidate = _closed(
        {
            **trust["properties"],
            "bundle_digest": _ref("sha256"),
            "schema_count": {"const": 31},
            "policy_count": {"const": 5},
        }
    )
    schema_descriptor = _closed(
        {
            "artifact_digest": _ref("sha256"),
            "canonical_path": _ref("repo_relative_posix_path"),
            "schema_sha256": _ref("sha256"),
            "schema_version": _ref("urn_id"),
            "self_digest_pointer": {
                "const": "/evidence_bundle_digest"
            },
        }
    )
    m051_contract = _closed(
        {
            "eval_profile_schema": _closed(
                {"schema_sha256": _ref("sha256")}
            ),
            "iteration_transition_schema": _closed(
                {"schema_sha256": _ref("sha256")}
            ),
            "sealed_holdout_required": {"const": True},
            "optimizer_may_read_sealed_labels": {"const": False},
            "optimizer_may_mutate_evaluator": {"const": False},
            "optimizer_may_mutate_profile": {"const": False},
            "optimizer_may_mutate_promotion_controller": {
                "const": False
            },
            "required_access_denial_attempt_codes": {
                "const": [row[0] for row in AUDIT_REQUIREMENTS]
            },
            "access_denial_recomputation_required": {"const": True},
        }
    )
    protection_contract = _closed(
        {
            "component_path": {
                "const": (
                    "CodexSkills/governance/release/"
                    "policy_protection.py"
                )
            },
            "component_source_binding_mode": {
                "const": "SUCCESSOR_EXTERNAL_TUPLE_REQUIRED"
            },
            "content_digest": _ref("sha256"),
            "observation_schema": schema_descriptor,
            "report_schema": schema_descriptor,
            "classifier_policy": _closed(
                {
                    "policy_id": {"const": VERSION_POLICY_V3_ID},
                    "policy_sha256": _ref("sha256"),
                }
            ),
            "protected_policy_codes": {"const": list(POLICY_CODES)},
            "protected_change_impact": {"const": "MAJOR"},
            "optimizer_protected_change_action": {"const": "BLOCK"},
            "independent_protected_change_action": {
                "const": "ISOLATE_TO_SEPARATE_MAJOR_RELEASE"
            },
            "report_recomputation_required": {"const": True},
            "m058_delegation_after_protection_pass_only": {
                "const": True
            },
            "m056_m058_source_mutation_permitted": {"const": False},
            "state_write_permitted": {"const": False},
            "public_artifact_write_permitted": {"const": False},
        }
    )
    source_trust = _closed(
        {
            "candidate_bundle": candidate,
            "registry_snapshot": _closed(
                {
                    **trust["properties"],
                    "registry_snapshot_digest": _ref("sha256"),
                }
            ),
            "m056_controller": predecessor,
            "m058_monitor": predecessor,
            "version_policy_v3": _closed(
                {
                    **trust["properties"],
                    "policy_id": {"const": VERSION_POLICY_V3_ID},
                    "policy_sha256": _ref("sha256"),
                }
            ),
            "repository_self_report_is_not_trust_root": {"const": True},
        }
    )
    registry_observation = _closed(
        {
            "identity_count": _ref("nonnegative_count"),
            "instance_count": _ref("nonnegative_count"),
            "version_count": _ref("nonnegative_count"),
            "base_champion_count": _ref("nonnegative_count"),
            "challenger_version_count": _ref("nonnegative_count"),
            "snapshot_status": {"const": "REGISTERED"},
            "real_protection_execution_permitted": {"const": False},
            "reason_code": {
                "const": "NO_REGISTERED_EVALUATED_CHAMPION_OR_CHALLENGER"
            },
        }
    )
    nonmutation = _closed(
        {
            "activation_forbidden": {"const": True},
            "auto_plane_unchanged": {"const": True},
            "candidate_bundle_unchanged": {"const": True},
            "canonical_publication_permitted": {"const": False},
            "registry_write_permitted": {"const": False},
            "release_write_permitted": {"const": False},
            "version_file_created": {"const": False},
        }
    )
    task_contract = _closed(
        {
            "dependency_task_ids": {"const": ["M-051", "M-056"]},
            "completed_task_ids": {
                "const": ["M-056", "M-057", "M-058", "M-059"]
            },
            "pending_task_ids": {"const": ["M-060"]},
            "required_output": {
                "const": "MAJOR_CLASSIFIER_AND_CHANGE_ISOLATION"
            },
            "done_gate": {
                "const": "OPTIMIZER_SELF_JUDGE_BLOCKED"
            },
        }
    )
    properties = {
        "artifact_digest": _ref("sha256"),
        "schema_version": {"const": READINESS_SCHEMA_ID},
        "protocol_revision": _ref("protocol_revision"),
        "status": {
            "const": (
                "DRAFT_NON_ACTIVE_EVALUATOR_RELEASE_POLICY_"
                "PROTECTION_READY"
            )
        },
        "owner_plane": {"const": "MECHANISM"},
        "digest_algorithm": {"const": "SHA-256"},
        "m051_dependency_contract": m051_contract,
        "protection_contract": protection_contract,
        "source_trust": source_trust,
        "registry_observation": registry_observation,
        "nonmutation": nonmutation,
        "task_contract": task_contract,
        "next_phase": {"const": NEXT_PHASE},
        "self_digest_pointer": {"const": "/artifact_digest"},
        "task_pack_revision": {"const": "v0.0.0.2"},
    }
    return {
        "$id": READINESS_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
        "title": "Mechanism M-059 evaluator/release protection readiness",
        "type": "object",
    }


def _trusted_candidate() -> ContractBundle:
    raw = _git_blob(CANDIDATE_GIT_OBJECT, CANDIDATE_MANIFEST_PATH)
    if _sha256(raw) != CANDIDATE_MANIFEST_RAW_SHA256:
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_CANDIDATE_MANIFEST_RAW_MISMATCH"
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


def _verify_predecessor(
    *,
    tagged_object: str,
    component_path: str,
    component_digest: str,
    readiness_path: str,
    readiness_digest: str,
) -> None:
    if (
        _sha256(_git_blob(tagged_object, component_path))
        != component_digest
        or _git_blob(tagged_object, component_path)
        != REPO_ROOT.joinpath(*component_path.split("/")).read_bytes()
        or _sha256(_git_blob(tagged_object, readiness_path))
        != readiness_digest
    ):
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_PREDECESSOR_TRUST_MISMATCH:"
            + component_path
        )


def _monitor_bundle(candidate: ContractBundle) -> ContractBundle:
    observation = _load(
        REPO_ROOT.joinpath(*M058_OBSERVATION_SCHEMA_PATH.split("/"))
    )
    report = _load(
        REPO_ROOT.joinpath(*M058_REPORT_SCHEMA_PATH.split("/"))
    )
    if (
        canonical_digest(observation) != M058_OBSERVATION_SCHEMA_SHA256
        or canonical_digest(report) != M058_REPORT_SCHEMA_SHA256
    ):
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_M058_SCHEMA_TRUST_MISMATCH"
        )
    return build_monitor_contract(
        candidate,
        observation,
        M058_OBSERVATION_SCHEMA_SHA256,
        report,
        M058_REPORT_SCHEMA_SHA256,
    )


def build_readiness() -> Mapping[str, Any]:
    candidate = _trusted_candidate()
    monitor_bundle = _monitor_bundle(candidate)
    observation_schema = build_observation_schema()
    report_schema = build_report_schema()
    protection_bundle = build_protection_contract(
        monitor_bundle,
        observation_schema,
        canonical_digest(observation_schema),
        report_schema,
        canonical_digest(report_schema),
    )
    _verify_predecessor(
        tagged_object=M056_GIT_OBJECT,
        component_path=M056_CONTROLLER_PATH,
        component_digest=M056_CONTROLLER_RAW_SHA256,
        readiness_path=M056_READINESS_PATH,
        readiness_digest=M056_READINESS_RAW_SHA256,
    )
    _verify_predecessor(
        tagged_object=M058_GIT_OBJECT,
        component_path=M058_MONITOR_PATH,
        component_digest=M058_MONITOR_RAW_SHA256,
        readiness_path=M058_READINESS_PATH,
        readiness_digest=M058_READINESS_RAW_SHA256,
    )
    policy_interface_raw = _git_blob(
        VERSION_POLICY_GIT_OBJECT,
        VERSION_POLICY_INTERFACE_PATH,
    )
    policy_raw = _git_blob(
        VERSION_POLICY_GIT_OBJECT,
        VERSION_POLICY_REPO_PATH,
    )
    policy = _load(VERSION_POLICY_PATH)
    if (
        _sha256(policy_interface_raw)
        != VERSION_POLICY_INTERFACE_RAW_SHA256
        or policy_raw != VERSION_POLICY_PATH.read_bytes()
        or canonical_digest(policy) != VERSION_POLICY_SHA256
    ):
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_VERSION_POLICY_TRUST_MISMATCH"
        )
    validate_version_policy_v3(policy)

    snapshot_raw = REGISTRY_SNAPSHOT_PATH.read_bytes()
    if (
        _sha256(snapshot_raw) != REGISTRY_SNAPSHOT_RAW_SHA256
        or _git_blob(
            REGISTRY_SNAPSHOT_GIT_OBJECT,
            REGISTRY_SNAPSHOT_REPO_PATH,
        )
        != snapshot_raw
    ):
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_REGISTRY_SNAPSHOT_TRUST_MISMATCH"
        )
    snapshot = _load(REGISTRY_SNAPSHOT_PATH)
    registry_view = build_registry_view(
        candidate,
        snapshot,
        expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
        expected_registry_snapshot_digest=snapshot[
            "registry_snapshot_digest"
        ],
    )
    if registry_view.base_champions or registry_view.challenger_version_uids:
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_REAL_REGISTRY_NOT_QUIESCENT"
        )
    if VERSION_PATH.exists():
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_ACTIVE_VERSION_FORBIDDEN"
        )

    eval_profile_schema = candidate.schemas[
        "urn:linzecolin:agentdatabase:skillops:schema:eval-profile:v1"
    ]
    iteration_schema = candidate.schemas[
        (
            "urn:linzecolin:agentdatabase:skillops:"
            "schema:iteration-transition:v1"
        )
    ]
    profile_properties = eval_profile_schema.get("properties", {})
    iteration_properties = iteration_schema.get("properties", {})
    if (
        profile_properties.get("sealed_holdout_required")
        != {"const": True}
        or profile_properties.get("optimizer_may_read_sealed_labels")
        != {"const": False}
        or profile_properties.get("optimizer_may_mutate_evaluator")
        != {"const": False}
        or profile_properties.get("optimizer_may_mutate_profile")
        != {"const": False}
        or profile_properties.get(
            "optimizer_may_mutate_promotion_controller"
        )
        != {"const": False}
        or "OPTIMIZER_EVALUATOR_ISOLATED"
        not in profile_properties.get(
            "hard_gate_codes",
            {},
        ).get("items", {}).get("enum", [])
        or "optimizer_evaluator_isolation_digest"
        not in iteration_properties
    ):
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_M051_DEPENDENCY_CONTRACT_MISMATCH"
        )
    readiness: Dict[str, Any] = {
        "artifact_digest": "0" * 64,
        "schema_version": READINESS_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "status": (
            "DRAFT_NON_ACTIVE_EVALUATOR_RELEASE_POLICY_PROTECTION_READY"
        ),
        "owner_plane": "MECHANISM",
        "digest_algorithm": "SHA-256",
        "m051_dependency_contract": {
            "eval_profile_schema": {
                "schema_sha256": canonical_digest(eval_profile_schema),
            },
            "iteration_transition_schema": {
                "schema_sha256": canonical_digest(iteration_schema),
            },
            "sealed_holdout_required": True,
            "optimizer_may_read_sealed_labels": False,
            "optimizer_may_mutate_evaluator": False,
            "optimizer_may_mutate_profile": False,
            "optimizer_may_mutate_promotion_controller": False,
            "required_access_denial_attempt_codes": [
                row[0] for row in AUDIT_REQUIREMENTS
            ],
            "access_denial_recomputation_required": True,
        },
        "protection_contract": {
            "component_path": (
                "CodexSkills/governance/release/policy_protection.py"
            ),
            "component_source_binding_mode": (
                "SUCCESSOR_EXTERNAL_TUPLE_REQUIRED"
            ),
            "content_digest": _sha256(PROTECTION_PATH.read_bytes()),
            "observation_schema": _schema_descriptor(
                path=(
                    "CodexSkills/governance/release/schemas/"
                    "evaluator-release-change-observation.schema.json"
                ),
                schema_id=OBSERVATION_SCHEMA_ID,
                schema=observation_schema,
                pointer=OBSERVATION_SELF_POINTER,
            ),
            "report_schema": _schema_descriptor(
                path=(
                    "CodexSkills/governance/release/schemas/"
                    "evaluator-release-protection-report.schema.json"
                ),
                schema_id=REPORT_SCHEMA_ID,
                schema=report_schema,
                pointer=REPORT_SELF_POINTER,
            ),
            "classifier_policy": {
                "policy_id": VERSION_POLICY_V3_ID,
                "policy_sha256": VERSION_POLICY_SHA256,
            },
            "protected_policy_codes": list(POLICY_CODES),
            "protected_change_impact": "MAJOR",
            "optimizer_protected_change_action": "BLOCK",
            "independent_protected_change_action": (
                "ISOLATE_TO_SEPARATE_MAJOR_RELEASE"
            ),
            "report_recomputation_required": True,
            "m058_delegation_after_protection_pass_only": True,
            "m056_m058_source_mutation_permitted": False,
            "state_write_permitted": False,
            "public_artifact_write_permitted": False,
        },
        "source_trust": {
            "candidate_bundle": {
                **_trust_descriptor(
                    artifact_digest=CANDIDATE_MANIFEST_RAW_SHA256,
                    canonical_path=CANDIDATE_MANIFEST_PATH,
                    expected_mode="CANDIDATE",
                    verified_git_object_id=CANDIDATE_GIT_OBJECT,
                ),
                "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
                "schema_count": len(candidate.schemas),
                "policy_count": len(candidate.policies),
            },
            "registry_snapshot": {
                **_trust_descriptor(
                    artifact_digest=REGISTRY_SNAPSHOT_RAW_SHA256,
                    canonical_path=REGISTRY_SNAPSHOT_REPO_PATH,
                    expected_mode="REGISTERED_READ_ONLY",
                    verified_git_object_id=REGISTRY_SNAPSHOT_GIT_OBJECT,
                ),
                "registry_snapshot_digest": (
                    registry_view.registry_snapshot_digest
                ),
            },
            "m056_controller": {
                **_trust_descriptor(
                    artifact_digest=M056_CONTROLLER_RAW_SHA256,
                    canonical_path=M056_CONTROLLER_PATH,
                    expected_mode="M056_IMMUTABLE_PREDECESSOR",
                    verified_git_object_id=M056_GIT_OBJECT,
                ),
                "readiness_artifact": {
                    "artifact_digest": M056_READINESS_RAW_SHA256,
                    "canonical_path": M056_READINESS_PATH,
                },
            },
            "m058_monitor": {
                **_trust_descriptor(
                    artifact_digest=M058_MONITOR_RAW_SHA256,
                    canonical_path=M058_MONITOR_PATH,
                    expected_mode="M058_IMMUTABLE_PREDECESSOR",
                    verified_git_object_id=M058_GIT_OBJECT,
                ),
                "readiness_artifact": {
                    "artifact_digest": M058_READINESS_RAW_SHA256,
                    "canonical_path": M058_READINESS_PATH,
                },
            },
            "version_policy_v3": {
                **_trust_descriptor(
                    artifact_digest=VERSION_POLICY_INTERFACE_RAW_SHA256,
                    canonical_path=VERSION_POLICY_INTERFACE_PATH,
                    expected_mode="DRAFT_NON_ACTIVE_VERSION_POLICY",
                    verified_git_object_id=VERSION_POLICY_GIT_OBJECT,
                ),
                "policy_id": VERSION_POLICY_V3_ID,
                "policy_sha256": VERSION_POLICY_SHA256,
            },
            "repository_self_report_is_not_trust_root": True,
        },
        "registry_observation": {
            "identity_count": len(registry_view.identity_uids),
            "instance_count": len(registry_view.instance_bindings),
            "version_count": len(registry_view.versions),
            "base_champion_count": len(registry_view.base_champions),
            "challenger_version_count": len(
                registry_view.challenger_version_uids
            ),
            "snapshot_status": snapshot["status"],
            "real_protection_execution_permitted": False,
            "reason_code": (
                "NO_REGISTERED_EVALUATED_CHAMPION_OR_CHALLENGER"
            ),
        },
        "nonmutation": {
            "activation_forbidden": True,
            "auto_plane_unchanged": True,
            "candidate_bundle_unchanged": True,
            "canonical_publication_permitted": False,
            "registry_write_permitted": False,
            "release_write_permitted": False,
            "version_file_created": False,
        },
        "task_contract": {
            "dependency_task_ids": ["M-051", "M-056"],
            "completed_task_ids": ["M-056", "M-057", "M-058", "M-059"],
            "pending_task_ids": ["M-060"],
            "required_output": "MAJOR_CLASSIFIER_AND_CHANGE_ISOLATION",
            "done_gate": (
                "OPTIMIZER_SELF_JUDGE_BLOCKED"
            ),
        },
        "next_phase": NEXT_PHASE,
        "self_digest_pointer": "/artifact_digest",
        "task_pack_revision": "v0.0.0.2",
    }
    readiness["artifact_digest"] = canonical_digest(
        readiness,
        "/artifact_digest",
    )
    readiness_schema = build_readiness_schema()
    schemas = dict(protection_bundle.schemas)
    if READINESS_SCHEMA_ID in schemas:
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_READINESS_SCHEMA_REBIND"
        )
    schemas[READINESS_SCHEMA_ID] = readiness_schema
    try:
        from CodexSkills.governance.tools.validate_mechanism import (
            build_registry,
        )

        registry, format_checker = build_registry(schemas)
        readiness_bundle = ContractBundle(
            schemas=schemas,
            registry=registry,
            format_checker=format_checker,
            self_digest_pointers={
                **protection_bundle.self_digest_pointers,
                READINESS_SCHEMA_ID: "/artifact_digest",
            },
            policies=protection_bundle.policies,
            protocol_revision=protection_bundle.protocol_revision,
        )
        validate_instance(
            readiness_bundle,
            readiness,
            READINESS_SCHEMA_ID,
            verify_digest=True,
            public=True,
        )
        scan_public_value(readiness, candidate.policies)
    except Exception as exc:
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_READINESS_INVALID:" + str(exc)
        ) from exc
    return readiness


def render_observation_schema() -> bytes:
    return _render(build_observation_schema())


def render_report_schema() -> bytes:
    return _render(build_report_schema())


def render_readiness_schema() -> bytes:
    return _render(build_readiness_schema())


def render_readiness() -> bytes:
    return _render(build_readiness())


def _write() -> None:
    OBSERVATION_SCHEMA_PATH.write_bytes(render_observation_schema())
    REPORT_SCHEMA_PATH.write_bytes(render_report_schema())
    READINESS_SCHEMA_PATH.write_bytes(render_readiness_schema())
    OUTPUT_PATH.write_bytes(render_readiness())


def _check() -> None:
    expected = {
        OBSERVATION_SCHEMA_PATH: render_observation_schema(),
        REPORT_SCHEMA_PATH: render_report_schema(),
        READINESS_SCHEMA_PATH: render_readiness_schema(),
        OUTPUT_PATH: render_readiness(),
    }
    drift = [
        path.as_posix()
        for path, raw in expected.items()
        if not path.exists() or path.read_bytes() != raw
    ]
    if drift:
        raise EvaluatorReleaseProtectionBuildError(
            "EVALUATOR_RELEASE_BYTE_DRIFT:" + ",".join(drift)
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        _write()
    else:
        _check()
    print(
        "EVALUATOR_RELEASE_PROTECTION_OK "
        "protected_policies=5 audit_denials=7 "
        "real_execution=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
