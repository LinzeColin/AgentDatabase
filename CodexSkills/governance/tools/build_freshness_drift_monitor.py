#!/usr/bin/env python3
"""Build/check non-active Mechanism M-058 freshness/drift evidence."""

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
    DIMENSION_CODES,
    OBSERVATION_SCHEMA_ID,
    OBSERVATION_SELF_POINTER,
    REPORT_SCHEMA_ID,
    REPORT_SELF_POINTER,
    RETEST_TRIGGER_CODES,
    build_monitor_contract,
)
from CodexSkills.governance.promotion.controller import (  # noqa: E402
    PROTOCOL_REVISION,
    build_registry_view,
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
MONITORING_DIR = GOVERNANCE_DIR / "monitoring"
OUTPUT_PATH = MONITORING_DIR / "freshness-drift-readiness.json"
OBSERVATION_SCHEMA_PATH = (
    MONITORING_DIR / "schemas" / "freshness-drift-observation.schema.json"
)
REPORT_SCHEMA_PATH = (
    MONITORING_DIR / "schemas" / "freshness-drift-report.schema.json"
)
READINESS_SCHEMA_PATH = (
    MONITORING_DIR / "schemas" / "freshness-drift-readiness.schema.json"
)
MONITOR_PATH = MONITORING_DIR / "freshness_drift.py"
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
    "schema:freshness-drift-readiness:v1"
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
M057_GIT_OBJECT = (
    "sha1:6d263e02ca6104abca5ae930b5eaa0944d8d5960"
)
M057_CONTROLLER_PATH = (
    "CodexSkills/governance/promotion/rollback_controller.py"
)
M057_CONTROLLER_RAW_SHA256 = (
    "44bd788038cadc6dd89810fbaebf9cefdc5351af96871e982193769eb2ececd2"
)
M057_READINESS_PATH = (
    "CodexSkills/governance/promotion/rollback-controller-readiness.json"
)
M057_READINESS_RAW_SHA256 = (
    "9ecdbc1f5cd103d6420cdd2d81b4ab14e94ce50668c6fabfe96ba05a9fd22494"
)
NEXT_PHASE = "MECHANISM_EVALUATOR_RELEASE_POLICY_PROTECTION"


class FreshnessDriftBuildError(ValueError):
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
        raise FreshnessDriftBuildError(
            "FRESHNESS_DRIFT_JSON_INVALID:" + path.as_posix()
        ) from exc
    if not isinstance(value, dict):
        raise FreshnessDriftBuildError(
            "FRESHNESS_DRIFT_JSON_ROOT_INVALID:" + path.as_posix()
        )
    return value


def _git_blob(tagged_object: str, relative_path: str) -> bytes:
    if tagged_object.count(":") != 1:
        raise FreshnessDriftBuildError(
            "FRESHNESS_DRIFT_GIT_OBJECT_INVALID"
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
        raise FreshnessDriftBuildError(
            "FRESHNESS_DRIFT_GIT_UNAVAILABLE"
        ) from exc
    if process.returncode != 0:
        raise FreshnessDriftBuildError(
            "FRESHNESS_DRIFT_GIT_BLOB_UNAVAILABLE:" + relative_path
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


def _digest_ref(uid_name: str) -> Dict[str, Any]:
    return _closed(
        {
            uid_name: _ref(uid_name),
            "artifact_digest": _ref("sha256"),
        }
    )


def build_observation_schema() -> Mapping[str, Any]:
    behavior_metric = _closed(
        {
            "dimension_code": {"enum": list(DIMENSION_CODES)},
            "score_bps": _ref("basis_points"),
            "evidence_digest": _ref("sha256"),
        }
    )
    latency_summary = _closed(
        {
            "sample_count": _ref("nonnegative_count"),
            "p50_milliseconds": _ref("nonnegative_count"),
            "p95_milliseconds": _ref("nonnegative_count"),
            "max_milliseconds": _ref("nonnegative_count"),
            "evidence_digest": _ref("sha256"),
        }
    )
    context = _closed(
        {
            "model_snapshot_digest": _ref("sha256"),
            "tool_manifest_digest": _ref("sha256"),
            "dataset_manifest_digests": {
                "items": _ref("sha256"),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "evaluator_manifest_digests": {
                "items": _ref("sha256"),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "policy_snapshot_digest": _ref("sha256"),
            "environment_fingerprint_digest": _ref("sha256"),
        }
    )
    dependency_ref = _closed(
        {"dependency_manifest_digest": _ref("sha256")}
    )
    properties = {
        "schema_version": {"const": OBSERVATION_SCHEMA_ID},
        "protocol_revision": _ref("protocol_revision"),
        "bundle_digest": _ref("sha256"),
        "observation_uid": _ref("typed_uid"),
        "skill_version_uid": _ref("skill_version_uid"),
        "skill_version_record_digest": _ref("sha256"),
        "scorecard_ref": _digest_ref("scorecard_uid"),
        "eval_profile_ref": _digest_ref("eval_profile_uid"),
        "context": context,
        "dependency_context": _closed(
            {
                "baseline": dependency_ref,
                "current": dependency_ref,
            }
        ),
        "behavior_metrics": {
            "items": behavior_metric,
            "maxItems": len(DIMENSION_CODES),
            "minItems": len(DIMENSION_CODES),
            "type": "array",
        },
        "latency": _closed(
            {
                "baseline": latency_summary,
                "current": latency_summary,
            }
        ),
        "critical_incident_count": _ref("nonnegative_count"),
        "critical_incident_evidence_digests": {
            "items": _ref("sha256"),
            "type": "array",
            "uniqueItems": True,
        },
        "observed_at": _ref("utc_z_timestamp"),
        "actor": {"const": "SKILLOPS_FRESHNESS_DRIFT_MONITOR"},
        "evidence_bundle_digest": _ref("sha256"),
    }
    return {
        "$id": OBSERVATION_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
        "title": "Freshness and drift observation",
        "type": "object",
    }


def build_report_schema() -> Mapping[str, Any]:
    alert = _closed(
        {
            "action_code": {"enum": ["INVESTIGATE", "REEVALUATE"]},
            "category": {
                "enum": [
                    "BEHAVIOR",
                    "CONTEXT",
                    "INCIDENT",
                    "LATENCY",
                    "POLICY_GAP",
                    "STALE",
                ]
            },
            "code": {
                "enum": [
                    "BEHAVIOR_SCORE_CHANGE",
                    "DATASET_CHANGE",
                    "DEPENDENCY_CHANGE",
                    "ENVIRONMENT_CHANGE",
                    "EVALUATOR_CHANGE",
                    "INCIDENT_OBSERVED",
                    "LATENCY_P95_REGRESSION",
                    "LATENCY_SAMPLE_INSUFFICIENT",
                    "MODEL_CHANGE",
                    "POLICY_CHANGE",
                    "PROFILE_RETEST_TRIGGER_GAP",
                    "SCORECARD_MAX_AGE_EXCEEDED",
                    "SCORECARD_STATE_STALE",
                    "SCORECARD_STATE_UNKNOWN",
                    "SCORECARD_VALIDITY_EXPIRED",
                    "SKILL_CHANGE",
                    "TOOL_CHANGE",
                ]
            },
            "evidence_digest": _ref("sha256"),
            "severity": {"enum": ["CRITICAL", "WARNING"]},
            "subject_codes": {
                "items": _ref("enum_code"),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
        }
    )
    freshness = _closed(
        {
            "state": {"enum": ["FRESH", "STALE", "UNKNOWN"]},
            "evaluated_at": _ref("utc_z_timestamp"),
            "deadline_at": _ref("utc_z_timestamp"),
            "freshness_valid_until": _nullable(_ref("calendar_date")),
            "age_microseconds": _ref("nonnegative_count"),
            "max_age_days": _ref("positive_count"),
        }
    )
    trigger_array = {
        "items": {"enum": list(RETEST_TRIGGER_CODES)},
        "type": "array",
        "uniqueItems": True,
    }
    properties = {
        "schema_version": {"const": REPORT_SCHEMA_ID},
        "protocol_revision": _ref("protocol_revision"),
        "bundle_digest": _ref("sha256"),
        "report_uid": _ref("typed_uid"),
        "mode": {"enum": ["MONITOR_ONLY", "PROMOTION_GATE"]},
        "skill_version_uid": _ref("skill_version_uid"),
        "scorecard_ref": _digest_ref("scorecard_uid"),
        "eval_profile_ref": _digest_ref("eval_profile_uid"),
        "observation_ref": _closed(
            {"artifact_digest": _ref("sha256")}
        ),
        "promotion_decision_ref": _nullable(
            _closed({"decision_digest": _ref("sha256")})
        ),
        "generated_at": _ref("utc_z_timestamp"),
        "freshness": freshness,
        "alerts": {
            "items": alert,
            "type": "array",
            "uniqueItems": True,
        },
        "retest_trigger_codes": trigger_array,
        "missing_profile_trigger_codes": trigger_array,
        "promotion_gate": _closed(
            {
                "status": {
                    "enum": ["BLOCKED", "NOT_EVALUATED", "PASS"]
                },
                "scorecard_effective_promotion_eligible": {
                    "type": "boolean"
                },
                "stale_score_independent_promotion_permitted": {
                    "const": False
                },
                "re_evaluation_required": {"type": "boolean"},
            }
        ),
        "actor": {"const": "SKILLOPS_FRESHNESS_DRIFT_MONITOR"},
        "evidence_bundle_digest": _ref("sha256"),
    }
    return {
        "$id": REPORT_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
        "title": "Freshness and drift report",
        "type": "object",
    }


def _schema_descriptor(
    *,
    path: str,
    schema_id: str,
    schema: Mapping[str, Any],
    pointer: str,
) -> Dict[str, Any]:
    raw = _render(schema)
    return {
        "artifact_digest": _sha256(raw),
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
    candidate_trust = _closed(
        {
            **trust["properties"],
            "bundle_digest": _ref("sha256"),
            "policy_count": {"const": 5},
            "schema_count": {"const": 31},
        }
    )
    registry_trust = _closed(
        {
            **trust["properties"],
            "registry_snapshot_digest": _ref("sha256"),
        }
    )
    predecessor_trust = _closed(
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
    monitor_contract = _closed(
        {
            "component_path": {
                "const": (
                    "CodexSkills/governance/monitoring/"
                    "freshness_drift.py"
                )
            },
            "component_source_binding_mode": {
                "const": "SUCCESSOR_EXTERNAL_TUPLE_REQUIRED"
            },
            "content_digest": _ref("sha256"),
            "observation_schema": schema_descriptor,
            "report_schema": schema_descriptor,
            "alert_categories": {
                "const": [
                    "BEHAVIOR",
                    "CONTEXT",
                    "INCIDENT",
                    "LATENCY",
                    "POLICY_GAP",
                    "STALE",
                ]
            },
            "report_recomputation_required": {"const": True},
            "promotion_gate_mode": {"const": "PROMOTION_GATE"},
            "stale_score_independent_promotion_permitted": {
                "const": False
            },
            "m056_delegation_after_monitor_gate_only": {"const": True},
            "m056_m057_source_mutation_permitted": {"const": False},
            "state_write_permitted": {"const": False},
            "public_artifact_write_permitted": {"const": False},
        }
    )
    nonmutation = _closed(
        {
            "activation_forbidden": {"const": True},
            "auto_plane_unchanged": {"const": True},
            "candidate_bundle_unchanged": {"const": True},
            "canonical_publication_permitted": {"const": False},
            "registry_write_permitted": {"const": False},
            "monitor_execution_permitted": {"const": False},
            "version_file_created": {"const": False},
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
            "real_monitor_execution_permitted": {"const": False},
            "reason_code": {
                "const": "NO_REGISTERED_EVALUATED_CHAMPION_OR_CHALLENGER"
            },
        }
    )
    source_trust = _closed(
        {
            "candidate_bundle": candidate_trust,
            "registry_snapshot": registry_trust,
            "m056_controller": predecessor_trust,
            "m057_controller": predecessor_trust,
            "repository_self_report_is_not_trust_root": {"const": True},
        }
    )
    task_contract = _closed(
        {
            "completed_task_ids": {
                "const": ["M-056", "M-057", "M-058"]
            },
            "pending_task_ids": {"const": ["M-059"]},
            "required_output": {
                "const": "STALE_BEHAVIOR_LATENCY_ALERTS"
            },
            "done_gate": {
                "const": "STALE_SCORE_CANNOT_INDEPENDENTLY_PROMOTE"
            },
        }
    )
    properties = {
        "artifact_digest": _ref("sha256"),
        "schema_version": {"const": READINESS_SCHEMA_ID},
        "protocol_revision": _ref("protocol_revision"),
        "status": {
            "const": "DRAFT_NON_ACTIVE_FRESHNESS_DRIFT_MONITOR_READY"
        },
        "owner_plane": {"const": "MECHANISM"},
        "digest_algorithm": {"const": "SHA-256"},
        "monitor_contract": monitor_contract,
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
        "title": "Mechanism M-058 freshness/drift readiness",
        "type": "object",
    }


def _trusted_candidate() -> ContractBundle:
    raw = _git_blob(CANDIDATE_GIT_OBJECT, CANDIDATE_MANIFEST_PATH)
    if _sha256(raw) != CANDIDATE_MANIFEST_RAW_SHA256:
        raise FreshnessDriftBuildError(
            "FRESHNESS_DRIFT_CANDIDATE_MANIFEST_RAW_MISMATCH"
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
        raise FreshnessDriftBuildError(
            "FRESHNESS_DRIFT_PREDECESSOR_TRUST_MISMATCH:"
            + component_path
        )


def build_readiness() -> Mapping[str, Any]:
    bundle = _trusted_candidate()
    observation_schema = build_observation_schema()
    report_schema = build_report_schema()
    monitor_bundle = build_monitor_contract(
        bundle,
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
        tagged_object=M057_GIT_OBJECT,
        component_path=M057_CONTROLLER_PATH,
        component_digest=M057_CONTROLLER_RAW_SHA256,
        readiness_path=M057_READINESS_PATH,
        readiness_digest=M057_READINESS_RAW_SHA256,
    )
    snapshot_raw = REGISTRY_SNAPSHOT_PATH.read_bytes()
    if (
        _sha256(snapshot_raw) != REGISTRY_SNAPSHOT_RAW_SHA256
        or _git_blob(
            REGISTRY_SNAPSHOT_GIT_OBJECT,
            REGISTRY_SNAPSHOT_REPO_PATH,
        )
        != snapshot_raw
    ):
        raise FreshnessDriftBuildError(
            "FRESHNESS_DRIFT_REGISTRY_SNAPSHOT_TRUST_MISMATCH"
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
        raise FreshnessDriftBuildError(
            "FRESHNESS_DRIFT_REAL_REGISTRY_NOT_QUIESCENT"
        )
    if VERSION_PATH.exists():
        raise FreshnessDriftBuildError(
            "FRESHNESS_DRIFT_ACTIVE_VERSION_FORBIDDEN"
        )

    observation_descriptor = _schema_descriptor(
        path=(
            "CodexSkills/governance/monitoring/schemas/"
            "freshness-drift-observation.schema.json"
        ),
        schema_id=OBSERVATION_SCHEMA_ID,
        schema=observation_schema,
        pointer=OBSERVATION_SELF_POINTER,
    )
    report_descriptor = _schema_descriptor(
        path=(
            "CodexSkills/governance/monitoring/schemas/"
            "freshness-drift-report.schema.json"
        ),
        schema_id=REPORT_SCHEMA_ID,
        schema=report_schema,
        pointer=REPORT_SELF_POINTER,
    )
    readiness: Dict[str, Any] = {
        "artifact_digest": "0" * 64,
        "schema_version": READINESS_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "status": "DRAFT_NON_ACTIVE_FRESHNESS_DRIFT_MONITOR_READY",
        "owner_plane": "MECHANISM",
        "digest_algorithm": "SHA-256",
        "monitor_contract": {
            "component_path": (
                "CodexSkills/governance/monitoring/freshness_drift.py"
            ),
            "component_source_binding_mode": (
                "SUCCESSOR_EXTERNAL_TUPLE_REQUIRED"
            ),
            "content_digest": _sha256(MONITOR_PATH.read_bytes()),
            "observation_schema": observation_descriptor,
            "report_schema": report_descriptor,
            "alert_categories": [
                "BEHAVIOR",
                "CONTEXT",
                "INCIDENT",
                "LATENCY",
                "POLICY_GAP",
                "STALE",
            ],
            "report_recomputation_required": True,
            "promotion_gate_mode": "PROMOTION_GATE",
            "stale_score_independent_promotion_permitted": False,
            "m056_delegation_after_monitor_gate_only": True,
            "m056_m057_source_mutation_permitted": False,
            "state_write_permitted": False,
            "public_artifact_write_permitted": False,
        },
        "source_trust": {
            "candidate_bundle": {
                "artifact_digest": CANDIDATE_MANIFEST_RAW_SHA256,
                "canonical_path": CANDIDATE_MANIFEST_PATH,
                "expected_mode": "CANDIDATE",
                "verified_git_object_id": CANDIDATE_GIT_OBJECT,
                "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
                "policy_count": len(bundle.policies),
                "schema_count": len(bundle.schemas),
            },
            "registry_snapshot": _trust_descriptor(
                artifact_digest=REGISTRY_SNAPSHOT_RAW_SHA256,
                canonical_path=REGISTRY_SNAPSHOT_REPO_PATH,
                expected_mode="REGISTERED_READ_ONLY",
                verified_git_object_id=REGISTRY_SNAPSHOT_GIT_OBJECT,
            ),
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
            "real_monitor_execution_permitted": False,
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
            "monitor_execution_permitted": False,
            "version_file_created": False,
        },
        "task_contract": {
            "completed_task_ids": ["M-056", "M-057", "M-058"],
            "pending_task_ids": ["M-059"],
            "required_output": "STALE_BEHAVIOR_LATENCY_ALERTS",
            "done_gate": "STALE_SCORE_CANNOT_INDEPENDENTLY_PROMOTE",
        },
        "next_phase": NEXT_PHASE,
        "self_digest_pointer": "/artifact_digest",
        "task_pack_revision": "v0.0.0.2",
    }
    readiness["source_trust"]["registry_snapshot"][
        "registry_snapshot_digest"
    ] = registry_view.registry_snapshot_digest
    for name, values in (
        (
            "m056_controller",
            (
                M056_CONTROLLER_RAW_SHA256,
                M056_CONTROLLER_PATH,
                "M056_IMMUTABLE_PREDECESSOR",
                M056_GIT_OBJECT,
                M056_READINESS_RAW_SHA256,
                M056_READINESS_PATH,
            ),
        ),
        (
            "m057_controller",
            (
                M057_CONTROLLER_RAW_SHA256,
                M057_CONTROLLER_PATH,
                "M057_IMMUTABLE_PREDECESSOR",
                M057_GIT_OBJECT,
                M057_READINESS_RAW_SHA256,
                M057_READINESS_PATH,
            ),
        ),
    ):
        (
            component_digest,
            component_path,
            expected_mode,
            git_object,
            readiness_digest,
            readiness_path,
        ) = values
        readiness["source_trust"][name] = {
            **_trust_descriptor(
                artifact_digest=component_digest,
                canonical_path=component_path,
                expected_mode=expected_mode,
                verified_git_object_id=git_object,
            ),
            "readiness_artifact": {
                "artifact_digest": readiness_digest,
                "canonical_path": readiness_path,
            },
        }
    readiness["artifact_digest"] = canonical_digest(
        readiness,
        "/artifact_digest",
    )
    validate_readiness(
        monitor_bundle,
        readiness,
    )
    return readiness


def validate_readiness(
    monitor_bundle: ContractBundle,
    readiness: Mapping[str, Any],
) -> None:
    schemas = dict(monitor_bundle.schemas)
    readiness_schema = build_readiness_schema()
    schemas[READINESS_SCHEMA_ID] = readiness_schema
    try:
        registry, format_checker = build_registry(schemas)
        extended = ContractBundle(
            schemas=schemas,
            registry=registry,
            format_checker=format_checker,
            self_digest_pointers={
                **monitor_bundle.self_digest_pointers,
                READINESS_SCHEMA_ID: "/artifact_digest",
            },
            policies=monitor_bundle.policies,
            protocol_revision=monitor_bundle.protocol_revision,
        )
        validate_instance(
            extended,
            readiness,
            READINESS_SCHEMA_ID,
            public=True,
        )
        scan_public_value(readiness, monitor_bundle.policies)
    except ContractError as exc:
        raise FreshnessDriftBuildError(
            "FRESHNESS_DRIFT_READINESS_INVALID:" + str(exc)
        ) from exc


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    expected = {
        OBSERVATION_SCHEMA_PATH: _render(build_observation_schema()),
        REPORT_SCHEMA_PATH: _render(build_report_schema()),
        READINESS_SCHEMA_PATH: _render(build_readiness_schema()),
        OUTPUT_PATH: _render(build_readiness()),
    }
    if args.write:
        for path, raw in expected.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        action = "FRESHNESS_DRIFT_MONITOR_GENERATED"
    else:
        mismatches = [
            path.as_posix()
            for path, raw in expected.items()
            if not path.is_file() or path.read_bytes() != raw
        ]
        if mismatches:
            raise FreshnessDriftBuildError(
                "FRESHNESS_DRIFT_MONITOR_BYTE_DRIFT:"
                + ",".join(mismatches)
            )
        action = "FRESHNESS_DRIFT_MONITOR_BYTE_EQUIVALENT"
    readiness = build_readiness()
    print(
        action
        + " artifact_digest="
        + readiness["artifact_digest"]
        + " observation_schema_sha256="
        + readiness["monitor_contract"]["observation_schema"][
            "schema_sha256"
        ]
        + " report_schema_sha256="
        + readiness["monitor_contract"]["report_schema"]["schema_sha256"]
        + " real_monitor_execution=false"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FreshnessDriftBuildError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
