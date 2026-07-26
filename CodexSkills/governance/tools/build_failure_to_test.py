#!/usr/bin/env python3
"""Build/check non-active Mechanism M-046 Failure-to-Test evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from CodexSkills.governance.evaluation.failure_to_test import (  # noqa: E402
    CANDIDATE_BUNDLE_DIGEST,
    FAILURE_CLASS_CODES,
    INCIDENT_SCHEMA_ID,
    PROTOCOL_REVISION,
    REGRESSION_SCHEMA_ID,
    ROOT_CAUSE_CODES,
    SELF_POINTER,
    SEVERITIES,
    convert_confirmed_incident,
    validate_confirmed_incident,
    validate_regression_case,
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
EVALUATION_DIR = GOVERNANCE_DIR / "evaluation"
SCHEMA_DIR = EVALUATION_DIR / "schemas"
COMPONENT_PATH = EVALUATION_DIR / "failure_to_test.py"
INCIDENT_PATH = EVALUATION_DIR / "confirmed-failure-incident.json"
REGRESSION_PATH = EVALUATION_DIR / "confirmed-regression-case.json"
READINESS_PATH = EVALUATION_DIR / "failure-to-test-readiness.json"
INCIDENT_SCHEMA_PATH = SCHEMA_DIR / "confirmed-failure-incident.schema.json"
REGRESSION_SCHEMA_PATH = (
    SCHEMA_DIR / "confirmed-regression-case.schema.json"
)
READINESS_SCHEMA_PATH = SCHEMA_DIR / "failure-to-test-readiness.schema.json"
VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

READINESS_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:failure-to-test-readiness:v1"
)
NEXT_PHASE = "MECHANISM_THREE_REPRESENTATIVE_PILOTS"
CANDIDATE_GIT_OBJECT = (
    "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5"
)
CANDIDATE_MANIFEST_PATH = (
    "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
)
CANDIDATE_MANIFEST_RAW_SHA256 = (
    "66ad125629cab71739ff2bc266219f995f7a45998936ca720c6db678ee77e65a"
)
PUBLIC_POLICY_ID = (
    "urn:linzecolin:agentdatabase:skillops:policy:public-value:v2"
)

FIXTURE_IDENTITY_UID = "ski_58AKTHBW3VQE0B7JM8WC6M1VPP"
FIXTURE_VERSION_UID = "skv_2HAJG2J7C1R3FFX194NRARWNKG"
FIXTURE_INCIDENT_UID = "inc_01ARZ3NDEKTSV4RRFFQ69G5FA1"
FIXTURE_REGRESSION_UID = "reg_01ARZ3NDEKTSV4RRFFQ69G5FA2"
FIXTURE_SOURCE_FACT_DIGESTS = ["1" * 64, "2" * 64]
FIXTURE_DETERMINISTIC_CHECK_DIGEST = "d" * 64
FIXTURE_SEALED_HOLDOUT_DIGEST = "e" * 64

REF = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:common-definitions:v1#/$defs/"
)


class FailureToTestBuildError(ValueError):
    """M-046 material cannot be rebuilt without weakening a gate."""


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
        raise FailureToTestBuildError(code) from exc
    if not isinstance(value, dict):
        raise FailureToTestBuildError(code)
    return value


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


def build_incident_schema() -> Mapping[str, Any]:
    triage = _closed(
        {
            "state": {"const": "PUBLIC_SAFE_METADATA_ONLY"},
            "raw_content_present": {"const": False},
            "personal_data_present": {"const": False},
            "sealed_holdout_content_present": {"const": False},
        }
    )
    root_cause = _closed(
        {
            "status": {"const": "CONFIRMED"},
            "cause_code": {"enum": list(ROOT_CAUSE_CODES)},
            "evidence_digests": _digest_array(),
        }
    )
    return {
        "$id": INCIDENT_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **_closed(
            {
                "schema_version": {"const": INCIDENT_SCHEMA_ID},
                "protocol_revision": _ref("protocol_revision"),
                "bundle_digest": _ref("sha256"),
                "incident_uid": _ref("typed_uid"),
                "skill_identity_uid": _ref("skill_identity_uid"),
                "skill_version_uid": _ref("skill_version_uid"),
                "severity": {"enum": list(SEVERITIES)},
                "status": {"const": "CONFIRMED"},
                "failure_class_code": {
                    "enum": list(FAILURE_CLASS_CODES)
                },
                "privacy_triage": triage,
                "root_cause": root_cause,
                "source_fact_digests": _digest_array(),
                "observed_at": _ref("utc_z_timestamp"),
                "artifact_digest": _ref("sha256"),
            }
        ),
        "title": "Public-safe confirmed failure incident",
    }


def build_regression_schema() -> Mapping[str, Any]:
    lineage = _closed(
        {
            "incident_uid": _ref("typed_uid"),
            "artifact_digest": _ref("sha256"),
            "source_fact_digests": _digest_array(),
            "root_cause_code": {"enum": list(ROOT_CAUSE_CODES)},
            "conversion_mode": {
                "const": "PUBLIC_SAFE_METADATA_ONLY"
            },
        }
    )
    sealed = _closed(
        {
            "sealed_holdout_manifest_digest": _ref("sha256"),
            "sealed_holdout_accessed": {"const": False},
            "sealed_holdout_labels_copied": {"const": False},
            "optimizer_visibility": {"const": "DENIED"},
        }
    )
    replay = _closed(
        {
            "deterministic": {"const": True},
            "side_effects_permitted": {"const": False},
            "raw_material_required": {"const": False},
            "evaluation_profile_mutation_permitted": {"const": False},
        }
    )
    return {
        "$id": REGRESSION_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **_closed(
            {
                "schema_version": {"const": REGRESSION_SCHEMA_ID},
                "protocol_revision": _ref("protocol_revision"),
                "bundle_digest": _ref("sha256"),
                "regression_case_uid": _ref("typed_uid"),
                "skill_identity_uid": _ref("skill_identity_uid"),
                "skill_version_uid": _ref("skill_version_uid"),
                "status": {"const": "CONFIRMED_REGRESSION"},
                "lineage": lineage,
                "sealed_boundary": sealed,
                "deterministic_check_manifest_digests": {
                    **_digest_array(),
                    "maxItems": 1,
                },
                "expected_outcome_code": {
                    "const": "DETECT_REGRESSION_AND_FAIL_CLOSED"
                },
                "replay_contract": replay,
                "created_at": _ref("utc_z_timestamp"),
                "artifact_digest": _ref("sha256"),
            }
        ),
        "title": "Confirmed public-safe regression case",
    }


def _extend_bundle(
    base: ContractBundle,
    additions: Mapping[str, Mapping[str, Any]],
) -> ContractBundle:
    schemas = dict(base.schemas)
    pointers = dict(base.self_digest_pointers)
    for schema_id, schema in additions.items():
        if schema_id in schemas:
            raise FailureToTestBuildError(
                "M046_SCHEMA_REBIND_FORBIDDEN:" + schema_id
            )
        schemas[schema_id] = schema
        pointers[schema_id] = SELF_POINTER
    try:
        registry, checker = build_registry(schemas)
    except ContractError as exc:
        raise FailureToTestBuildError(
            "M046_SCHEMA_CLOSURE_INVALID:" + str(exc)
        ) from exc
    return ContractBundle(
        schemas=schemas,
        registry=registry,
        format_checker=checker,
        self_digest_pointers=pointers,
        policies=base.policies,
        protocol_revision=base.protocol_revision,
    )


def build_fixture_incident() -> Mapping[str, Any]:
    value: Dict[str, Any] = {
        "schema_version": INCIDENT_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        "incident_uid": FIXTURE_INCIDENT_UID,
        "skill_identity_uid": FIXTURE_IDENTITY_UID,
        "skill_version_uid": FIXTURE_VERSION_UID,
        "severity": "MAJOR",
        "status": "CONFIRMED",
        "failure_class_code": "DETERMINISTIC_CORRECTNESS",
        "privacy_triage": {
            "state": "PUBLIC_SAFE_METADATA_ONLY",
            "raw_content_present": False,
            "personal_data_present": False,
            "sealed_holdout_content_present": False,
        },
        "root_cause": {
            "status": "CONFIRMED",
            "cause_code": "DETERMINISTIC_OUTPUT_MISMATCH",
            "evidence_digests": [FIXTURE_SOURCE_FACT_DIGESTS[0]],
        },
        "source_fact_digests": list(FIXTURE_SOURCE_FACT_DIGESTS),
        "observed_at": "2026-07-26T01:00:00.000000Z",
        "artifact_digest": "0" * 64,
    }
    value["artifact_digest"] = canonical_digest(value, SELF_POINTER)
    return value


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
    incident: Mapping[str, Any],
    regression: Mapping[str, Any],
    incident_schema: Mapping[str, Any],
    regression_schema: Mapping[str, Any],
    bundle: ContractBundle,
) -> Mapping[str, Any]:
    public_policy = bundle.policies.get(PUBLIC_POLICY_ID)
    if not isinstance(public_policy, dict):
        raise FailureToTestBuildError("M046_PUBLIC_POLICY_NOT_TRUSTED")
    incident_schema_raw = _render(incident_schema)
    regression_schema_raw = _render(regression_schema)
    incident_raw = _render(incident)
    regression_raw = _render(regression)
    value: Dict[str, Any] = {
        "schema_version": READINESS_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        "status": (
            "DRAFT_NON_ACTIVE_FAILURE_TO_TEST_CONVERSION_READY_"
            "SHADOW_FIXTURE_ONLY"
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
            "public_value_policy": {
                "policy_id": PUBLIC_POLICY_ID,
                "policy_sha256": canonical_digest(public_policy),
                "expected_mode": "CANDIDATE_MEMBER",
            },
            "repository_self_report_is_not_trust_root": True,
        },
        "dependency_contract": {
            "task_id": "M-045",
            "standalone_repository_artifact_present": False,
            "functional_input_contract_embedded": True,
            "privacy_triage_required": True,
            "root_cause_confirmation_required": True,
            "raw_data_publication_permitted": False,
            "dependency_status": (
                "FUNCTIONAL_CONTRACT_RECONSTRUCTED_FAIL_CLOSED"
            ),
        },
        "implementation_contract": {
            "component_path": (
                "CodexSkills/governance/evaluation/failure_to_test.py"
            ),
            "content_digest": _sha256(COMPONENT_PATH.read_bytes()),
            "capability_mode": "PURE_IMMUTABLE_OBJECTS_ONLY",
            "incident_schema": _descriptor(
                INCIDENT_SCHEMA_ID,
                INCIDENT_SCHEMA_PATH,
                incident_schema_raw,
                incident_schema,
            ),
            "regression_schema": _descriptor(
                REGRESSION_SCHEMA_ID,
                REGRESSION_SCHEMA_PATH,
                regression_schema_raw,
                regression_schema,
            ),
            "caller_output_fields_accepted": False,
            "filesystem_capability_present": False,
            "git_capability_present": False,
            "network_capability_present": False,
            "raw_material_read_capability_present": False,
            "sealed_holdout_read_capability_present": False,
            "state_capability_present": False,
            "publisher_capability_present": False,
        },
        "shadow_fixture": {
            "mode": "SYNTHETIC_PUBLIC_SAFE_METADATA_ONLY",
            "incident": {
                "canonical_path": INCIDENT_PATH.relative_to(
                    REPO_ROOT
                ).as_posix(),
                "content_digest": _sha256(incident_raw),
                "artifact_digest": incident["artifact_digest"],
            },
            "regression_case": {
                "canonical_path": REGRESSION_PATH.relative_to(
                    REPO_ROOT
                ).as_posix(),
                "content_digest": _sha256(regression_raw),
                "artifact_digest": regression["artifact_digest"],
            },
            "lineage_closed": True,
            "root_cause_confirmed": True,
            "sealed_holdout_contaminated": False,
            "sealed_holdout_accessed": False,
            "sealed_holdout_labels_copied": False,
            "production_incident_converted": False,
        },
        "nonmutation": {
            "auto_plane_unchanged": True,
            "openai_database_unchanged": True,
            "candidate_bundle_unchanged": True,
            "evaluation_profile_mutated": False,
            "real_incident_read": False,
            "raw_material_read": False,
            "sealed_holdout_read": False,
            "notification_sent": False,
            "state_write_permitted": False,
            "canonical_publication_permitted": False,
            "activation_forbidden": True,
            "version_file_created": False,
        },
        "task_contract": {
            "dependency_task_ids": ["M-045"],
            "implemented_task_ids": ["M-046"],
            "pending_task_ids": ["M-068"],
            "required_output_code": (
                "CONFIRMED_REGRESSION_CASE_WITH_LINEAGE"
            ),
            "done_gate": "SEALED_HOLDOUT_NEVER_CONTAMINATED",
        },
        "schema_closure_count": 34,
        "policy_count": 5,
        "production_conversion_ready": False,
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
        "title": "Mechanism M-046 Failure-to-Test readiness",
    }


def _documents() -> Mapping[Path, bytes]:
    incident_schema = build_incident_schema()
    regression_schema = build_regression_schema()
    incident = build_fixture_incident()
    regression = convert_confirmed_incident(
        incident,
        regression_case_uid=FIXTURE_REGRESSION_UID,
        deterministic_check_manifest_digest=(
            FIXTURE_DETERMINISTIC_CHECK_DIGEST
        ),
        sealed_holdout_manifest_digest=FIXTURE_SEALED_HOLDOUT_DIGEST,
        created_at="2026-07-26T01:00:01.000000Z",
    )
    validate_confirmed_incident(incident)
    validate_regression_case(regression, incident)

    base = load_au040_acceptance().bundle
    provisional = _extend_bundle(
        base,
        {
            INCIDENT_SCHEMA_ID: incident_schema,
            REGRESSION_SCHEMA_ID: regression_schema,
        },
    )
    readiness = _build_readiness(
        incident,
        regression,
        incident_schema,
        regression_schema,
        provisional,
    )
    readiness_schema = build_readiness_schema(readiness)
    contract = _extend_bundle(
        provisional,
        {READINESS_SCHEMA_ID: readiness_schema},
    )
    if len(contract.schemas) != 34 or len(contract.policies) != 5:
        raise FailureToTestBuildError(
            "M046_SCHEMA_OR_POLICY_COUNT_INVALID"
        )
    for value, schema_id in (
        (incident, INCIDENT_SCHEMA_ID),
        (regression, REGRESSION_SCHEMA_ID),
        (readiness, READINESS_SCHEMA_ID),
    ):
        validate_instance(
            contract,
            value,
            schema_id,
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            verify_digest=True,
            public=True,
        )
        scan_public_value(value, contract.policies)
    return {
        INCIDENT_SCHEMA_PATH: _render(incident_schema),
        REGRESSION_SCHEMA_PATH: _render(regression_schema),
        READINESS_SCHEMA_PATH: _render(readiness_schema),
        INCIDENT_PATH: _render(incident),
        REGRESSION_PATH: _render(regression),
        READINESS_PATH: _render(readiness),
    }


def _write() -> None:
    for path, raw in _documents().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def _check() -> None:
    for path, expected in _documents().items():
        if not path.is_file() or path.is_symlink():
            raise FailureToTestBuildError(
                "M046_GENERATED_FILE_INVALID:" + str(path)
            )
        if path.read_bytes() != expected:
            raise FailureToTestBuildError(
                "M046_GENERATED_BYTE_DRIFT:" + str(path)
            )
    if VERSION_PATH.exists():
        raise FailureToTestBuildError(
            "M046_VERSION_MUST_REMAIN_ABSENT"
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
        regression = _load(
            _documents()[REGRESSION_PATH],
            "M046_REGRESSION_FIXTURE_INVALID",
        )
        print(
            "FAILURE_TO_TEST_OK "
            "lineage_closed=true sealed_contaminated=false "
            "production_ready=false regression="
            + regression["artifact_digest"]
        )
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
