"""Pure deterministic Shadow pilots for Mechanism Task Pack M-068.

The harness projects three rounds of evidence for a deterministic sync Skill,
a same-name multi-source Skill, and a high-risk iterative Skill.  It consumes
only immutable public-safe Registry and Mechanism dependency objects.  It does
not execute a Skill, read source contents, access sealed labels, write state,
mutate Registry, send a notification, publish, migrate, or activate.
"""

from __future__ import annotations

import copy
import re
from typing import Any, Dict, Mapping, Sequence, Tuple

from CodexSkills.governance.promotion.rollback_controller import (
    REQUIRED_VERIFICATION_KINDS,
)
from CodexSkills.governance.tools.canonical_json import canonical_digest


SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
PROTOCOL_REVISION = (
    "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
)
CANDIDATE_BUNDLE_DIGEST = (
    "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
)
PILOT_SCHEMA_ID = SCHEMA_PREFIX + "representative-pilot-evidence:v1"
REGISTRY_SCHEMA_ID = SCHEMA_PREFIX + "registry-snapshot:v1"
FAILURE_READINESS_SCHEMA_ID = (
    SCHEMA_PREFIX + "failure-to-test-readiness:v1"
)
REGRESSION_SCHEMA_ID = SCHEMA_PREFIX + "confirmed-regression-case:v1"
ROLLBACK_READINESS_SCHEMA_ID = (
    SCHEMA_PREFIX + "rollback-controller-readiness:v1"
)
MIGRATION_READINESS_SCHEMA_ID = (
    SCHEMA_PREFIX + "read-only-migration-cutover-readiness:v1"
)
SELF_POINTER = "/artifact_digest"
DRILL_SELF_POINTER = "/evidence_bundle_digest"

PILOT_CLASSES = (
    "DETERMINISTIC_SYNC",
    "SAME_NAME_MULTI_SOURCE",
    "HIGH_RISK_ITERATIVE",
)
PILOT_UIDS = {
    "DETERMINISTIC_SYNC": "pil_01ARZ3NDEKTSV4RRFFQ69G5FA1",
    "SAME_NAME_MULTI_SOURCE": "pil_01ARZ3NDEKTSV4RRFFQ69G5FA2",
    "HIGH_RISK_ITERATIVE": "pil_01ARZ3NDEKTSV4RRFFQ69G5FA3",
}
PILOT_SPECS = {
    "DETERMINISTIC_SYNC": {
        "canonical_name": "skill-github-sync",
        "members": (("CODEX", "codex/skill-github-sync"),),
        "pilot_gate_codes": ("SYNC_IDEMPOTENCY",),
    },
    "SAME_NAME_MULTI_SOURCE": {
        "canonical_name": "agent-reach",
        "members": (
            ("AGENTS", "agents/agent-reach"),
            ("CODEX", "codex/agent-reach"),
        ),
        "pilot_gate_codes": (
            "OWNER_REVIEW_REQUIRED_NO_AUTO_MERGE",
            "SAME_NAME_DISTINCT_IDENTITY_PRESERVED",
        ),
    },
    "HIGH_RISK_ITERATIVE": {
        "canonical_name": "km-bid-evolve",
        "members": (("CODEX", "codex/km-bid-evolve"),),
        "pilot_gate_codes": (
            "FAILURE_TO_TEST_LINEAGE",
            "NO_AUTONOMOUS_PROMOTION",
            "SEALED_HOLDOUT_ISOLATION",
        ),
    },
}
COMMON_GATE_CODES = (
    "REGISTRY_REFERENCE_CLOSURE",
    "ROLLBACK_DRILL_CLOSURE",
    "ZERO_SIDE_EFFECT_SHADOW",
)
COMMON_PRODUCTION_BLOCKERS = (
    "BINDING_ELIGIBLE_VERSION_COUNT_ZERO",
    "M065_CUTOVER_BLOCKED",
    "REAL_CHAMPION_ABSENT",
    "REAL_PROVIDER_NOTIFICATION_ABSENT",
    "REGISTRY_VERSIONS_QUARANTINED",
)

DEPENDENCY_KEYS = (
    "failure_readiness",
    "regression_case",
    "rollback_readiness",
    "migration_readiness",
)
EXPECTED_DEPENDENCY_SCHEMAS = {
    "failure_readiness": FAILURE_READINESS_SCHEMA_ID,
    "regression_case": REGRESSION_SCHEMA_ID,
    "rollback_readiness": ROLLBACK_READINESS_SCHEMA_ID,
    "migration_readiness": MIGRATION_READINESS_SCHEMA_ID,
}
EXPECTED_DEPENDENCY_STATUS = {
    "failure_readiness": (
        "DRAFT_NON_ACTIVE_FAILURE_TO_TEST_CONVERSION_READY_"
        "SHADOW_FIXTURE_ONLY"
    ),
    "regression_case": "CONFIRMED_REGRESSION",
    "rollback_readiness": (
        "DRAFT_NON_ACTIVE_ROLLBACK_REVOCATION_CONTROLLER_READY"
    ),
    "migration_readiness": (
        "DRAFT_NON_ACTIVE_READ_ONLY_MIGRATION_CUTOVER_"
        "IMPLEMENTED_BLOCKED"
    ),
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UID_RE = re.compile(r"^[a-z][a-z0-9]{1,11}_[0-7][0-9A-HJKMNP-TV-Z]{25}$")
REPO_PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")


class RepresentativePilotError(ValueError):
    """A Registry, dependency, cycle, or rollback gate failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> None:
    raise RepresentativePilotError(code)


def _digest(value: Any, code: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        _fail(code)
    return value


def _exact_fields(
    value: Mapping[str, Any],
    fields: Sequence[str],
    code: str,
) -> None:
    if not isinstance(value, dict) or set(value) != set(fields):
        _fail(code)


def _validate_dependency(
    key: str,
    value: Mapping[str, Any],
) -> None:
    if key not in EXPECTED_DEPENDENCY_SCHEMAS or not isinstance(value, dict):
        _fail("PILOT_DEPENDENCY_INVALID:" + key)
    if (
        value.get("schema_version") != EXPECTED_DEPENDENCY_SCHEMAS[key]
        or value.get("protocol_revision") != PROTOCOL_REVISION
        or value.get("status") != EXPECTED_DEPENDENCY_STATUS[key]
    ):
        _fail("PILOT_DEPENDENCY_STATE_INVALID:" + key)
    if (
        "bundle_digest" in value
        and value["bundle_digest"] != CANDIDATE_BUNDLE_DIGEST
    ):
        _fail("PILOT_DEPENDENCY_BUNDLE_INVALID:" + key)
    digest = _digest(
        value.get("artifact_digest"),
        "PILOT_DEPENDENCY_DIGEST_INVALID:" + key,
    )
    if digest != canonical_digest(value, SELF_POINTER):
        _fail("PILOT_DEPENDENCY_SELF_DIGEST_MISMATCH:" + key)


def _validate_dependencies(
    dependencies: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Mapping[str, Any]]:
    if not isinstance(dependencies, dict) or set(dependencies) != set(
        DEPENDENCY_KEYS
    ):
        _fail("PILOT_DEPENDENCY_SET_INCOMPLETE")
    result = copy.deepcopy(dict(dependencies))
    for key in DEPENDENCY_KEYS:
        _validate_dependency(key, result[key])

    failure = result["failure_readiness"]
    regression = result["regression_case"]
    rollback = result["rollback_readiness"]
    migration = result["migration_readiness"]
    if (
        failure.get("shadow_fixture", {})
        .get("regression_case", {})
        .get("artifact_digest")
        != regression["artifact_digest"]
        or failure.get("shadow_fixture", {}).get(
            "sealed_holdout_contaminated"
        )
        is not False
        or failure.get("shadow_fixture", {}).get(
            "sealed_holdout_accessed"
        )
        is not False
        or failure.get("shadow_fixture", {}).get(
            "sealed_holdout_labels_copied"
        )
        is not False
        or failure.get("production_conversion_ready") is not False
    ):
        _fail("PILOT_FAILURE_TO_TEST_CLOSURE_INVALID")
    if (
        rollback.get("controller_contract", {}).get(
            "history_rewrite_permitted"
        )
        is not False
        or rollback.get("registry_observation", {}).get(
            "base_champion_count"
        )
        != 0
        or rollback.get("registry_observation", {}).get(
            "real_rollback_revocation_execution_permitted"
        )
        is not False
    ):
        _fail("PILOT_ROLLBACK_DEPENDENCY_INVALID")
    current = migration.get("current_evidence", {})
    if (
        current.get("decision") != "BLOCKED"
        or current.get("cutover_mode") != "SHADOW_ONLY"
        or current.get("delete_budget") != 0
        or current.get("local_data_mutation_performed") is not False
        or migration.get("real_execution_permitted") is not False
    ):
        _fail("PILOT_MIGRATION_DEPENDENCY_INVALID")
    return result


def _validate_registry(
    snapshot: Mapping[str, Any],
) -> Mapping[str, Any]:
    if not isinstance(snapshot, dict):
        _fail("PILOT_REGISTRY_INVALID")
    if (
        snapshot.get("schema_version") != REGISTRY_SCHEMA_ID
        or snapshot.get("protocol_revision") != PROTOCOL_REVISION
        or snapshot.get("bundle_digest") != CANDIDATE_BUNDLE_DIGEST
        or snapshot.get("status") != "REGISTERED"
        or snapshot.get("same_name_auto_merge_permitted") is not False
    ):
        _fail("PILOT_REGISTRY_STATE_INVALID")
    digest = _digest(
        snapshot.get("registry_snapshot_digest"),
        "PILOT_REGISTRY_DIGEST_INVALID",
    )
    if digest != canonical_digest(snapshot, "/registry_snapshot_digest"):
        _fail("PILOT_REGISTRY_SELF_DIGEST_MISMATCH")
    counts = snapshot.get("counts")
    if (
        not isinstance(counts, dict)
        or counts.get("identity_count") != len(snapshot.get("identities", ()))
        or counts.get("instance_count") != len(snapshot.get("instances", ()))
        or counts.get("version_count") != len(snapshot.get("versions", ()))
        or counts.get("identity_count") != 89
        or counts.get("instance_count") != 89
        or counts.get("version_count") != 89
        or counts.get("binding_eligible_version_count") != 0
        or counts.get("quarantined_version_count") != 89
    ):
        _fail("PILOT_REGISTRY_COUNT_OR_ELIGIBILITY_INVALID")
    return copy.deepcopy(snapshot)


def _single(values: Sequence[Mapping[str, Any]], code: str) -> Mapping[str, Any]:
    if len(values) != 1:
        _fail(code)
    return values[0]


def _member(
    snapshot: Mapping[str, Any],
    canonical_name: str,
    source_class: str,
    source_relative_path: str,
) -> Mapping[str, Any]:
    if (
        not isinstance(source_relative_path, str)
        or REPO_PATH_RE.fullmatch(source_relative_path) is None
        or source_relative_path.startswith("/")
        or ".." in source_relative_path.split("/")
    ):
        _fail("PILOT_SOURCE_PATH_INVALID")
    instances = [
        value
        for value in snapshot["instances"]
        if value.get("record", {}).get("source_class") == source_class
        and value.get("record", {}).get("source_relative_path")
        == source_relative_path
    ]
    instance = _single(instances, "PILOT_INSTANCE_SELECTION_NOT_UNIQUE")
    instance_record = instance["record"]
    identities = [
        value
        for value in snapshot["identities"]
        if value.get("record", {}).get("skill_identity_uid")
        == instance_record["skill_identity_uid"]
    ]
    identity = _single(
        identities,
        "PILOT_IDENTITY_REFERENCE_NOT_UNIQUE",
    )
    identity_record = identity["record"]
    if (
        identity_record.get("canonical_name") != canonical_name
        or identity_record.get("lifecycle_status") != "QUARANTINED"
        or instance_record.get("lifecycle_status") != "QUARANTINED"
        or len(instance_record.get("version_uids", ())) != 1
    ):
        _fail("PILOT_IDENTITY_INSTANCE_STATE_INVALID")
    version_uid = instance_record["version_uids"][0]
    versions = [
        value
        for value in snapshot["versions"]
        if value.get("record", {}).get("skill_version_uid") == version_uid
        and value.get("record", {}).get("skill_instance_uid")
        == instance_record["skill_instance_uid"]
    ]
    version = _single(versions, "PILOT_VERSION_REFERENCE_NOT_UNIQUE")
    version_record = version["record"]
    if (
        version_record.get("lifecycle_status") != "QUARANTINED"
        or version_record.get("trust_tier") != "UNVERIFIED"
        or version_record.get("eval_profile_uid") is not None
        or any(
            state != "UNKNOWN"
            for state in version_record.get("permissions", {}).values()
        )
    ):
        _fail("PILOT_VERSION_NOT_FAIL_CLOSED")
    return {
        "source_class": source_class,
        "source_relative_path": source_relative_path,
        "skill_identity_uid": identity_record["skill_identity_uid"],
        "identity_ref": {
            "artifact_digest": _digest(
                identity["artifact_digest"],
                "PILOT_IDENTITY_DIGEST_INVALID",
            )
        },
        "skill_instance_uid": instance_record["skill_instance_uid"],
        "instance_ref": {
            "artifact_digest": _digest(
                instance["artifact_digest"],
                "PILOT_INSTANCE_DIGEST_INVALID",
            )
        },
        "skill_version_uid": version_record["skill_version_uid"],
        "version_ref": {
            "version_record_digest": _digest(
                version["version_record_digest"],
                "PILOT_VERSION_DIGEST_INVALID",
            )
        },
        "source_fingerprint_digest": _digest(
            instance_record["source_fingerprint_digest"],
            "PILOT_SOURCE_FINGERPRINT_INVALID",
        ),
        "content_digest": _digest(
            version_record["content_digest"],
            "PILOT_CONTENT_DIGEST_INVALID",
        ),
        "lifecycle_status": "QUARANTINED",
        "trust_tier": "UNVERIFIED",
        "binding_eligible": False,
        "eval_profile_present": False,
        "permissions_resolved": False,
    }


def _identity_resolution(
    snapshot: Mapping[str, Any],
    canonical_name: str,
    members: Sequence[Mapping[str, Any]],
    pilot_class: str,
) -> Mapping[str, Any]:
    registry_uids = sorted(
        value["record"]["skill_identity_uid"]
        for value in snapshot["identities"]
        if value.get("record", {}).get("canonical_name") == canonical_name
    )
    selected_uids = sorted(
        member["skill_identity_uid"] for member in members
    )
    if (
        not registry_uids
        or len(registry_uids) != len(set(registry_uids))
        or len(selected_uids) != len(set(selected_uids))
        or not set(selected_uids).issubset(set(registry_uids))
    ):
        _fail("PILOT_IDENTITY_RESOLUTION_INVALID")
    merge_candidates = [
        value
        for value in snapshot["identity_merge_candidates"]
        if value.get("canonical_name") == canonical_name
    ]
    if len(registry_uids) == 1:
        if merge_candidates:
            _fail("PILOT_SINGLE_IDENTITY_MERGE_CANDIDATE_INVALID")
        owner_review = False
    else:
        candidate = _single(
            merge_candidates,
            "PILOT_MERGE_CANDIDATE_NOT_UNIQUE",
        )
        if (
            sorted(candidate.get("identity_uids", ())) != registry_uids
            or candidate.get("reason_code") != "OWNER_REVIEW_REQUIRED"
        ):
            _fail("PILOT_MERGE_CANDIDATE_CLOSURE_INVALID")
        owner_review = True
    if (
        pilot_class == "SAME_NAME_MULTI_SOURCE"
        and selected_uids != registry_uids
    ):
        _fail("PILOT_DUPLICATE_IDENTITY_SELECTION_INCOMPLETE")
    return {
        "registry_identity_uids": registry_uids,
        "selected_identity_uids": selected_uids,
        "registry_identity_count": len(registry_uids),
        "selected_identity_count": len(selected_uids),
        "same_name_auto_merge_permitted": False,
        "owner_review_required": owner_review,
    }


def _shadow_result_digest(
    pilot_class: str,
    members: Sequence[Mapping[str, Any]],
    dependencies: Mapping[str, Mapping[str, Any]],
    registry_snapshot_digest: str,
) -> str:
    return canonical_digest(
        {
            "domain": "SKILLOPS_REPRESENTATIVE_PILOT_RESULT_V1",
            "pilot_class": pilot_class,
            "registry_snapshot_digest": registry_snapshot_digest,
            "selected_versions": [
                {
                    "skill_version_uid": member["skill_version_uid"],
                    "version_record_digest": member["version_ref"][
                        "version_record_digest"
                    ],
                    "content_digest": member["content_digest"],
                }
                for member in members
            ],
            "dependency_artifact_digests": [
                dependencies[key]["artifact_digest"]
                for key in DEPENDENCY_KEYS
            ],
        }
    )


def _verification_digest(
    pilot_class: str,
    cycle_index: int,
    kind: str,
    shadow_evidence_digest: str,
) -> str:
    return canonical_digest(
        {
            "domain": "SKILLOPS_REPRESENTATIVE_ROLLBACK_VERIFICATION_V1",
            "pilot_class": pilot_class,
            "cycle_index": cycle_index,
            "kind": kind,
            "shadow_evidence_digest": shadow_evidence_digest,
        }
    )


def _rollback_drill(
    pilot_class: str,
    cycle_index: int,
    shadow_evidence_digest: str,
) -> Mapping[str, Any]:
    value: Dict[str, Any] = {
        "status": "SHADOW_PASS",
        "mode": "SYNTHETIC_PRE_WRITE_NO_STATE",
        "verification_evidence_refs": [
            {
                "kind": kind,
                "artifact_digest": _verification_digest(
                    pilot_class,
                    cycle_index,
                    kind,
                    shadow_evidence_digest,
                ),
            }
            for kind in REQUIRED_VERIFICATION_KINDS
        ],
        "synthetic_prior_champion_restorable": True,
        "real_registry_champion_present": False,
        "history_rewrite_performed": False,
        "state_write_observed": False,
        "notification_sent": False,
        "production_drill": False,
        "evidence_bundle_digest": "0" * 64,
    }
    value["evidence_bundle_digest"] = canonical_digest(
        value,
        DRILL_SELF_POINTER,
    )
    return value


def _gate_evidence(
    code: str,
    *,
    dependencies: Mapping[str, Mapping[str, Any]],
    registry_snapshot_digest: str,
    shadow_evidence_digest: str,
    drill_digest: str,
) -> Tuple[str, ...]:
    mapping = {
        "REGISTRY_REFERENCE_CLOSURE": (registry_snapshot_digest,),
        "ROLLBACK_DRILL_CLOSURE": (drill_digest,),
        "ZERO_SIDE_EFFECT_SHADOW": (
            dependencies["migration_readiness"]["artifact_digest"],
        ),
        "SYNC_IDEMPOTENCY": (shadow_evidence_digest,),
        "OWNER_REVIEW_REQUIRED_NO_AUTO_MERGE": (
            registry_snapshot_digest,
        ),
        "SAME_NAME_DISTINCT_IDENTITY_PRESERVED": (
            registry_snapshot_digest,
        ),
        "FAILURE_TO_TEST_LINEAGE": (
            dependencies["regression_case"]["artifact_digest"],
        ),
        "NO_AUTONOMOUS_PROMOTION": (
            dependencies["rollback_readiness"]["artifact_digest"],
        ),
        "SEALED_HOLDOUT_ISOLATION": (
            dependencies["failure_readiness"]["artifact_digest"],
        ),
    }
    if code not in mapping:
        _fail("PILOT_GATE_CODE_UNSUPPORTED:" + code)
    return tuple(sorted(set(mapping[code])))


def _cycle(
    pilot_class: str,
    cycle_index: int,
    members: Sequence[Mapping[str, Any]],
    dependencies: Mapping[str, Mapping[str, Any]],
    registry_snapshot_digest: str,
    shadow_evidence_digest: str,
) -> Mapping[str, Any]:
    drill = _rollback_drill(
        pilot_class,
        cycle_index,
        shadow_evidence_digest,
    )
    codes = sorted(
        set(COMMON_GATE_CODES)
        | set(PILOT_SPECS[pilot_class]["pilot_gate_codes"])
    )
    value: Dict[str, Any] = {
        "cycle_index": cycle_index,
        "mode": "DETERMINISTIC_SHADOW_METADATA_ONLY",
        "member_version_uids": sorted(
            member["skill_version_uid"] for member in members
        ),
        "shadow_evidence_digest": shadow_evidence_digest,
        "gate_results": [
            {
                "gate_code": code,
                "critical": True,
                "status": "PASS",
                "evidence_digests": list(
                    _gate_evidence(
                        code,
                        dependencies=dependencies,
                        registry_snapshot_digest=(
                            registry_snapshot_digest
                        ),
                        shadow_evidence_digest=shadow_evidence_digest,
                        drill_digest=drill["evidence_bundle_digest"],
                    )
                ),
            }
            for code in codes
        ],
        "rollback_drill": drill,
        "side_effect_count": 0,
        "registry_write_count": 0,
        "state_write_count": 0,
        "notification_count": 0,
        "publication_count": 0,
        "evidence_digest": "0" * 64,
    }
    value["evidence_digest"] = canonical_digest(value, "/evidence_digest")
    return value


def build_pilot(
    pilot_class: str,
    snapshot: Mapping[str, Any],
    dependencies: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    """Build one exact three-cycle public-safe Shadow pilot."""

    if pilot_class not in PILOT_CLASSES:
        _fail("PILOT_CLASS_UNSUPPORTED")
    registry = _validate_registry(snapshot)
    deps = _validate_dependencies(dependencies)
    spec = PILOT_SPECS[pilot_class]
    members = [
        _member(
            registry,
            spec["canonical_name"],
            source_class,
            source_path,
        )
        for source_class, source_path in spec["members"]
    ]
    identity_resolution = _identity_resolution(
        registry,
        spec["canonical_name"],
        members,
        pilot_class,
    )
    if pilot_class == "HIGH_RISK_ITERATIVE":
        regression = deps["regression_case"]
        selected = members[0]
        if (
            regression.get("skill_identity_uid")
            != selected["skill_identity_uid"]
            or regression.get("skill_version_uid")
            != selected["skill_version_uid"]
            or regression.get("sealed_boundary", {}).get(
                "sealed_holdout_accessed"
            )
            is not False
            or regression.get("sealed_boundary", {}).get(
                "sealed_holdout_labels_copied"
            )
            is not False
        ):
            _fail("PILOT_HIGH_RISK_REGRESSION_BINDING_INVALID")
    snapshot_digest = registry["registry_snapshot_digest"]
    stable_result = _shadow_result_digest(
        pilot_class,
        members,
        deps,
        snapshot_digest,
    )
    cycles = [
        _cycle(
            pilot_class,
            index,
            members,
            deps,
            snapshot_digest,
            stable_result,
        )
        for index in (1, 2, 3)
    ]
    blockers = list(COMMON_PRODUCTION_BLOCKERS)
    if pilot_class == "HIGH_RISK_ITERATIVE":
        blockers.append("REAL_EVALUATION_PROFILE_ABSENT")
    blockers.sort()
    value: Dict[str, Any] = {
        "schema_version": PILOT_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        "pilot_uid": PILOT_UIDS[pilot_class],
        "pilot_class": pilot_class,
        "canonical_name": spec["canonical_name"],
        "execution_mode": "DETERMINISTIC_SHADOW_METADATA_ONLY",
        "status": "SHADOW_COMPLETE_PRODUCTION_BLOCKED",
        "registry_snapshot_digest": snapshot_digest,
        "members": members,
        "identity_resolution": identity_resolution,
        "cycles": cycles,
        "summary": {
            "cycle_count": 3,
            "clean_cycle_count": 3,
            "all_shadow_critical_gates_passed": True,
            "all_shadow_rollback_drills_passed": True,
            "three_cycle_result_stable": (
                len(
                    {
                        cycle["shadow_evidence_digest"]
                        for cycle in cycles
                    }
                )
                == 1
            ),
            "production_critical_gates_passed": False,
            "production_pilot_executed": False,
            "production_blocker_codes": blockers,
        },
        "artifact_digest": "0" * 64,
    }
    value["artifact_digest"] = canonical_digest(value, SELF_POINTER)
    return value


def build_all_pilots(
    snapshot: Mapping[str, Any],
    dependencies: Mapping[str, Mapping[str, Any]],
) -> Tuple[Mapping[str, Any], ...]:
    """Return the three pilot artifacts in frozen class order."""

    return tuple(
        build_pilot(pilot_class, snapshot, dependencies)
        for pilot_class in PILOT_CLASSES
    )


def validate_pilot(
    pilot: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    dependencies: Mapping[str, Mapping[str, Any]],
) -> None:
    """Reject caller fields by exact full-object recomputation."""

    if not isinstance(pilot, dict):
        _fail("PILOT_EVIDENCE_INVALID")
    pilot_class = pilot.get("pilot_class")
    expected = build_pilot(pilot_class, snapshot, dependencies)
    if pilot != expected:
        _fail("PILOT_EVIDENCE_RECOMPUTATION_MISMATCH")
