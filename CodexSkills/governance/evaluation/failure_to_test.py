"""Pure Failure-to-Test conversion for Mechanism Task Pack M-046.

The converter accepts only a confirmed, public-safe incident envelope and
returns immutable regression-case metadata.  It never reads raw incident
material, sealed-holdout content or labels, the filesystem, Git, runtime
state, or a network.  A caller cannot use this module to publish, mutate an
evaluation profile, or execute a regression test.
"""

from __future__ import annotations

import copy
import datetime as dt
import re
from typing import Any, Dict, Mapping, Sequence, Tuple

from CodexSkills.governance.tools.canonical_json import canonical_digest


SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
PROTOCOL_REVISION = (
    "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
)
CANDIDATE_BUNDLE_DIGEST = (
    "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
)
INCIDENT_SCHEMA_ID = SCHEMA_PREFIX + "confirmed-failure-incident:v1"
REGRESSION_SCHEMA_ID = SCHEMA_PREFIX + "confirmed-regression-case:v1"
SELF_POINTER = "/artifact_digest"
UTC_Z_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

FAILURE_CLASS_CODES = (
    "DETERMINISTIC_CORRECTNESS",
    "PERMISSION_BOUNDARY",
    "PRIVACY_GUARD",
    "ROUTING_REGRESSION",
)
ROOT_CAUSE_CODES = (
    "CONTRACT_MISMATCH",
    "DETERMINISTIC_OUTPUT_MISMATCH",
    "PERMISSION_OVERREACH",
    "PRIVACY_POLICY_VIOLATION",
    "ROUTING_FALSE_TRIGGER",
)
SEVERITIES = ("MAJOR", "CRITICAL")
REQUIRED_INCIDENT_FIELDS = (
    "schema_version",
    "protocol_revision",
    "bundle_digest",
    "incident_uid",
    "skill_identity_uid",
    "skill_version_uid",
    "severity",
    "status",
    "failure_class_code",
    "privacy_triage",
    "root_cause",
    "source_fact_digests",
    "observed_at",
    "artifact_digest",
)
REQUIRED_REGRESSION_FIELDS = (
    "schema_version",
    "protocol_revision",
    "bundle_digest",
    "regression_case_uid",
    "skill_identity_uid",
    "skill_version_uid",
    "status",
    "lineage",
    "sealed_boundary",
    "deterministic_check_manifest_digests",
    "expected_outcome_code",
    "replay_contract",
    "created_at",
    "artifact_digest",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TYPED_UID_RE = re.compile(
    r"^[a-z][a-z0-9]{1,11}_[0-7][0-9A-HJKMNP-TV-Z]{25}$"
)
SKILL_IDENTITY_RE = re.compile(r"^ski_[0-7][0-9A-HJKMNP-TV-Z]{25}$")
SKILL_VERSION_RE = re.compile(r"^skv_[0-7][0-9A-HJKMNP-TV-Z]{25}$")


class FailureToTestError(ValueError):
    """The incident-to-regression conversion failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> None:
    raise FailureToTestError(code)


def _exact_fields(
    value: Mapping[str, Any],
    expected: Sequence[str],
    code: str,
) -> None:
    if not isinstance(value, dict) or set(value) != set(expected):
        _fail(code)


def _digest(value: Any, code: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        _fail(code)
    return value


def _timestamp(value: Any, code: str) -> str:
    if not isinstance(value, str):
        _fail(code)
    try:
        parsed = dt.datetime.strptime(value, UTC_Z_FORMAT)
    except ValueError as exc:
        raise FailureToTestError(code) from exc
    if parsed.strftime(UTC_Z_FORMAT) != value:
        _fail(code)
    return value


def _sorted_unique_digests(values: Any, code: str) -> Tuple[str, ...]:
    if (
        not isinstance(values, list)
        or not values
        or values != sorted(values)
        or len(values) != len(set(values))
    ):
        _fail(code)
    return tuple(_digest(value, code) for value in values)


def validate_confirmed_incident(
    incident: Mapping[str, Any],
) -> None:
    """Validate the closed public-safe input envelope."""

    _exact_fields(
        incident,
        REQUIRED_INCIDENT_FIELDS,
        "FAILURE_INCIDENT_FIELDS_INVALID",
    )
    if (
        incident["schema_version"] != INCIDENT_SCHEMA_ID
        or incident["protocol_revision"] != PROTOCOL_REVISION
        or incident["bundle_digest"] != CANDIDATE_BUNDLE_DIGEST
    ):
        _fail("FAILURE_INCIDENT_CONTEXT_INVALID")
    if (
        not isinstance(incident["incident_uid"], str)
        or TYPED_UID_RE.fullmatch(incident["incident_uid"]) is None
        or not incident["incident_uid"].startswith("inc_")
        or not isinstance(incident["skill_identity_uid"], str)
        or SKILL_IDENTITY_RE.fullmatch(incident["skill_identity_uid"])
        is None
        or not isinstance(incident["skill_version_uid"], str)
        or SKILL_VERSION_RE.fullmatch(incident["skill_version_uid"]) is None
    ):
        _fail("FAILURE_INCIDENT_REFERENCE_INVALID")
    if (
        incident["severity"] not in SEVERITIES
        or incident["status"] != "CONFIRMED"
        or incident["failure_class_code"] not in FAILURE_CLASS_CODES
    ):
        _fail("FAILURE_INCIDENT_CLASSIFICATION_INVALID")

    triage = incident["privacy_triage"]
    _exact_fields(
        triage,
        (
            "state",
            "raw_content_present",
            "personal_data_present",
            "sealed_holdout_content_present",
        ),
        "FAILURE_INCIDENT_TRIAGE_FIELDS_INVALID",
    )
    if triage != {
        "state": "PUBLIC_SAFE_METADATA_ONLY",
        "raw_content_present": False,
        "personal_data_present": False,
        "sealed_holdout_content_present": False,
    }:
        _fail("FAILURE_INCIDENT_PRIVACY_TRIAGE_NOT_SAFE")

    cause = incident["root_cause"]
    _exact_fields(
        cause,
        ("status", "cause_code", "evidence_digests"),
        "FAILURE_INCIDENT_ROOT_CAUSE_FIELDS_INVALID",
    )
    if (
        cause["status"] != "CONFIRMED"
        or cause["cause_code"] not in ROOT_CAUSE_CODES
    ):
        _fail("FAILURE_INCIDENT_ROOT_CAUSE_UNCONFIRMED")
    cause_digests = _sorted_unique_digests(
        cause["evidence_digests"],
        "FAILURE_INCIDENT_ROOT_CAUSE_EVIDENCE_INVALID",
    )
    source_digests = _sorted_unique_digests(
        incident["source_fact_digests"],
        "FAILURE_INCIDENT_SOURCE_FACTS_INVALID",
    )
    if not set(cause_digests).issubset(set(source_digests)):
        _fail("FAILURE_INCIDENT_ROOT_CAUSE_LINEAGE_INCOMPLETE")
    _timestamp(incident["observed_at"], "FAILURE_INCIDENT_TIME_INVALID")
    digest = _digest(
        incident["artifact_digest"],
        "FAILURE_INCIDENT_DIGEST_INVALID",
    )
    if digest != canonical_digest(incident, SELF_POINTER):
        _fail("FAILURE_INCIDENT_SELF_DIGEST_MISMATCH")


def convert_confirmed_incident(
    incident: Mapping[str, Any],
    *,
    regression_case_uid: str,
    deterministic_check_manifest_digest: str,
    sealed_holdout_manifest_digest: str,
    created_at: str,
) -> Mapping[str, Any]:
    """Derive one public-safe regression case without reading test content."""

    validate_confirmed_incident(incident)
    if (
        not isinstance(regression_case_uid, str)
        or TYPED_UID_RE.fullmatch(regression_case_uid) is None
        or not regression_case_uid.startswith("reg_")
    ):
        _fail("REGRESSION_CASE_UID_INVALID")
    deterministic_digest = _digest(
        deterministic_check_manifest_digest,
        "REGRESSION_CHECK_DIGEST_INVALID",
    )
    holdout_digest = _digest(
        sealed_holdout_manifest_digest,
        "REGRESSION_HOLDOUT_DIGEST_INVALID",
    )
    if (
        holdout_digest == deterministic_digest
        or holdout_digest in incident["source_fact_digests"]
        or holdout_digest in incident["root_cause"]["evidence_digests"]
    ):
        _fail("REGRESSION_SEALED_HOLDOUT_CONTAMINATION")
    _timestamp(created_at, "REGRESSION_CREATED_AT_INVALID")
    if created_at < incident["observed_at"]:
        _fail("REGRESSION_CREATED_BEFORE_INCIDENT")

    value: Dict[str, Any] = {
        "schema_version": REGRESSION_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        "regression_case_uid": regression_case_uid,
        "skill_identity_uid": incident["skill_identity_uid"],
        "skill_version_uid": incident["skill_version_uid"],
        "status": "CONFIRMED_REGRESSION",
        "lineage": {
            "incident_uid": incident["incident_uid"],
            "artifact_digest": incident["artifact_digest"],
            "source_fact_digests": copy.deepcopy(
                incident["source_fact_digests"]
            ),
            "root_cause_code": incident["root_cause"]["cause_code"],
            "conversion_mode": "PUBLIC_SAFE_METADATA_ONLY",
        },
        "sealed_boundary": {
            "sealed_holdout_manifest_digest": holdout_digest,
            "sealed_holdout_accessed": False,
            "sealed_holdout_labels_copied": False,
            "optimizer_visibility": "DENIED",
        },
        "deterministic_check_manifest_digests": [deterministic_digest],
        "expected_outcome_code": "DETECT_REGRESSION_AND_FAIL_CLOSED",
        "replay_contract": {
            "deterministic": True,
            "side_effects_permitted": False,
            "raw_material_required": False,
            "evaluation_profile_mutation_permitted": False,
        },
        "created_at": created_at,
        "artifact_digest": "0" * 64,
    }
    value["artifact_digest"] = canonical_digest(value, SELF_POINTER)
    return value


def validate_regression_case(
    regression_case: Mapping[str, Any],
    incident: Mapping[str, Any],
) -> None:
    """Recompute every caller-visible conversion field."""

    _exact_fields(
        regression_case,
        REQUIRED_REGRESSION_FIELDS,
        "REGRESSION_CASE_FIELDS_INVALID",
    )
    deterministic = regression_case.get(
        "deterministic_check_manifest_digests"
    )
    if not isinstance(deterministic, list) or len(deterministic) != 1:
        _fail("REGRESSION_CHECK_SET_INVALID")
    boundary = regression_case.get("sealed_boundary")
    if not isinstance(boundary, dict):
        _fail("REGRESSION_SEALED_BOUNDARY_INVALID")
    expected = convert_confirmed_incident(
        incident,
        regression_case_uid=regression_case.get("regression_case_uid"),
        deterministic_check_manifest_digest=deterministic[0],
        sealed_holdout_manifest_digest=boundary.get(
            "sealed_holdout_manifest_digest"
        ),
        created_at=regression_case.get("created_at"),
    )
    if regression_case != expected:
        _fail("REGRESSION_CASE_RECOMPUTATION_MISMATCH")
