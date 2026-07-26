#!/usr/bin/env python3
"""Build/check Mechanism v2/v3 consumer-first readiness evidence."""

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

from CodexSkills.governance.release.version_policy_v3.consumer import (  # noqa: E402
    CANDIDATE_MANIFEST_PATH,
    DRAFT_INTERFACE_MODE,
    DRAFT_INTERFACE_PATH,
    PREDECESSOR_SELECTION_MODE,
    SUCCESSOR_SELECTION_MODE,
    VERSION_POLICY_CONSUMER_READINESS_SCHEMA_ID,
    VersionPolicyDraftTrustTuple,
    load_trusted_version_policies,
)
from CodexSkills.governance.release.version_policy_v3.contract import (  # noqa: E402
    PROTOCOL_REVISION,
    SCHEDULE_CANDIDATES,
    TASK_PACK_REVISION,
    UNRESOLVED_SCHEDULE_CODE,
    VERSION_POLICY_V2_ID,
    VERSION_POLICY_V3_ID,
)
from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_mechanism import (  # noqa: E402
    TrustTuple,
    scan_public_value,
)


GOVERNANCE_DIR = REPO_ROOT / "CodexSkills" / "governance"
RELEASE_DIR = GOVERNANCE_DIR / "release" / "version_policy_v3"
OUTPUT_PATH = RELEASE_DIR / "consumer-readiness.json"
SCHEMA_PATH = RELEASE_DIR / "schemas" / "consumer-readiness.schema.json"
ACTIVE_VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

CANDIDATE_GIT_OBJECT = (
    "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5"
)
CANDIDATE_BUNDLE_DIGEST = (
    "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
)
CANDIDATE_MANIFEST_RAW_SHA256 = (
    "66ad125629cab71739ff2bc266219f995f7a45998936ca720c6db678ee77e65a"
)
DRAFT_GIT_OBJECT = (
    "sha1:07f7925185f7e1486f808042a10c383ba52d572f"
)
DRAFT_INTERFACE_RAW_SHA256 = (
    "0fa8303981a1b263c835e74cc864fb114c4e1d4eb1a5e8c317c140754b84b8f7"
)
AUTO_GIT_OBJECT = (
    "sha1:1c829553996c792e46cedc4570b30545fba9e071"
)
AUTO_RUNTIME_INTERFACE_PATH = (
    "CodexSkills/registry/auto/runtime-interface.json"
)
AUTO_RUNTIME_INTERFACE_RAW_SHA256 = (
    "3e91bf41c9550fa48264db3b72ee102b0acec65b883374d2735fbd7169801d9e"
)
CONTROL_INTERFACE_PATH = (
    "CodexSkills/governance/activation/control-interface.json"
)
CONTROL_INTERFACE_RAW_SHA256 = (
    "8caf7e5dbb922714c3afa39040e55b8a83015ea0f02de153e19cc3010b0e0e1a"
)
NEXT_PHASE = "AUTO_VERSION_POLICY_V3_DUAL_READ_INTEGRATION"

MECHANISM_CONSUMER_PATHS = (
    (
        "MECHANISM_VERSION_POLICY_DUAL_READ_LOADER",
        "CodexSkills/governance/release/version_policy_v3/consumer.py",
        "V2_V3_DUAL_READ",
    ),
    (
        "MECHANISM_VERSION_POLICY_SEMANTIC_VALIDATOR",
        "CodexSkills/governance/release/version_policy_v3/contract.py",
        "V2_V3_COMPATIBILITY",
    ),
)
AUTO_CONSUMER_PATHS = (
    (
        "AUTO_SCHEDULE_POLICY_CONSUMER",
        "CodexSkills/registry/auto/runtime/schedule.py",
        "V2_ONLY",
    ),
    (
        "AUTO_NOTIFICATION_POLICY_CONSUMER",
        "CodexSkills/registry/auto/runtime/notification.py",
        "V2_ONLY",
    ),
    (
        "AUTO_RUNTIME_TRUST_BOOTSTRAP",
        "CodexSkills/registry/auto/runtime/bootstrap.py",
        "CANDIDATE_BUNDLE_ONLY",
    ),
    (
        "AUTO_SHARED_CONTRACT_LOADER",
        "CodexSkills/registry/auto/tools/validate_auto.py",
        "CANDIDATE_BUNDLE_ONLY",
    ),
)


class VersionPolicyConsumerReadinessBuildError(ValueError):
    """Readiness material cannot be reproduced without weakening a gate."""


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


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_sha(value: Mapping[str, Any]) -> str:
    return _sha256(canonicalize_object(value))


def _load(path: Path) -> Mapping[str, Any]:
    try:
        value = parse_json_bytes(path.read_bytes())
    except Exception as exc:
        raise VersionPolicyConsumerReadinessBuildError(
            "VERSION_POLICY_CONSUMER_READINESS_JSON_INVALID:"
            + path.as_posix()
        ) from exc
    if not isinstance(value, dict):
        raise VersionPolicyConsumerReadinessBuildError(
            "VERSION_POLICY_CONSUMER_READINESS_JSON_ROOT_INVALID:"
            + path.as_posix()
        )
    return value


def _git_blob(tagged_object: str, relative_path: str) -> bytes:
    object_id = tagged_object.split(":", 1)[1]
    try:
        result = subprocess.run(
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
        raise VersionPolicyConsumerReadinessBuildError(
            "VERSION_POLICY_CONSUMER_READINESS_GIT_UNAVAILABLE"
        ) from exc
    if result.returncode != 0:
        raise VersionPolicyConsumerReadinessBuildError(
            "VERSION_POLICY_CONSUMER_READINESS_GIT_BLOB_UNAVAILABLE:"
            + relative_path
        )
    return result.stdout


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
    canonicalization = _closed(
        {
            "duplicate_keys": {"const": "REJECT"},
            "encoding": {"const": "UTF-8"},
            "input_profile": {"const": "I_JSON"},
            "scheme": {"const": "RFC8785_JCS"},
            "self_digest_exclusion": {
                "const": "EXACT_DECLARED_JSON_POINTER_ONLY"
            },
            "unicode_normalization": {"const": "NONE"},
        }
    )
    trust_entry = _closed(
        {
            "artifact_digest": _ref("sha256"),
            "canonical_path": _ref("repo_relative_posix_path"),
            "expected_mode": {
                "enum": ["CANDIDATE", DRAFT_INTERFACE_MODE]
            },
            "verified_git_object_id": _ref("git_object_id"),
        }
    )
    candidate_trust = _closed(
        {
            **trust_entry["properties"],
            "bundle_digest": _ref("sha256"),
            "policy_count": {"const": 5},
            "schema_count": {"const": 31},
        }
    )
    source_trust = _closed(
        {
            "predecessor_candidate": candidate_trust,
            "repository_self_report_is_not_trust_root": {"const": True},
            "v3_draft": trust_entry,
        }
    )
    consumer_item = _closed(
        {
            "component_id": {
                "enum": [
                    row[0]
                    for row in (
                        *MECHANISM_CONSUMER_PATHS,
                        *AUTO_CONSUMER_PATHS,
                    )
                ]
            },
            "content_digest": _ref("sha256"),
            "observed_support": {
                "enum": [
                    "CANDIDATE_BUNDLE_ONLY",
                    "V2_ONLY",
                    "V2_V3_COMPATIBILITY",
                    "V2_V3_DUAL_READ",
                ]
            },
            "owner_plane": {"enum": ["AUTO", "MECHANISM"]},
            "relative_path": _ref("repo_relative_posix_path"),
            "required_action": {
                "enum": ["AUTO_DUAL_READ_INTEGRATION", "NONE"]
            },
            "source_binding_mode": {
                "enum": [
                    "IMMUTABLE_GIT_OBJECT",
                    "SUCCESSOR_EXTERNAL_TUPLE_REQUIRED",
                ]
            },
            "source_git_object_id": {
                "anyOf": [_ref("git_object_id"), {"type": "null"}]
            },
        }
    )
    compatibility = _closed(
        {
            "auto_consumer_first_verified": {"const": False},
            "candidate_materialization_permitted": {"const": False},
            "change_class": {"const": "MAJOR"},
            "compatibility_mode": {
                "const": "CONSUMER_FIRST_REPLACEMENT"
            },
            "cross_plane_consumer_first_complete": {"const": False},
            "daily_srv_separation_explicit": {"const": True},
            "existing_v2_major_trigger_codes_preserved": {"const": True},
            "mechanism_consumer_first_verified": {"const": True},
            "missing_major_trigger_codes_closed": {
                "const": [
                    "AUTOMATIC_SIDE_EFFECT_CHANGE",
                    "EVALUATOR_OR_HOLDOUT_CHANGE",
                    "HARD_GATE_CHANGE",
                    "MIGRATION_OR_DELETE_SEMANTICS_CHANGE",
                    "NETWORK_OR_PERMISSION_CHANGE",
                    "PRIVACY_POLICY_CHANGE",
                ]
            },
            "notification_semantics_preserved": {"const": True},
            "predecessor_policy_accepted": {"const": True},
            "schedule_authority_resolved": {"const": False},
        }
    )
    consumer_contract = _closed(
        {
            "accepted_policy_ids": {
                "const": [VERSION_POLICY_V2_ID, VERSION_POLICY_V3_ID]
            },
            "auto_dual_read_verified": {"const": False},
            "cross_plane_consumer_first_complete": {"const": False},
            "hybrid_selection_forbidden": {"const": True},
            "mechanism_dual_read_verified": {"const": True},
            "mechanism_schedule_fail_closed_verified": {"const": True},
            "predecessor_selection_mode": {
                "const": PREDECESSOR_SELECTION_MODE
            },
            "selection_mode_required": {"const": True},
            "stronger_impact_downgrade_allowed": {"const": False},
            "successor_selection_mode": {
                "const": SUCCESSOR_SELECTION_MODE
            },
            "unknown_or_duplicate_trigger_action": {
                "const": "FAIL_CLOSED"
            },
            "unknown_policy_id_action": {"const": "FAIL_CLOSED"},
        }
    )
    schedule = _closed(
        {
            "activation_permitted": {"const": False},
            "authority_state": {"const": "UNRESOLVED"},
            "candidate_local_times": {
                "const": list(SCHEDULE_CANDIDATES)
            },
            "conflict_code": {"const": UNRESOLVED_SCHEDULE_CODE},
            "selected_local_time": {"type": "null"},
            "timezone": {"const": "Australia/Sydney"},
        }
    )
    nonmutation = _closed(
        {
            "activation_forbidden": {"const": True},
            "candidate_bundle_unchanged": {"const": True},
            "canonical_publication_permitted": {"const": False},
            "control_interface": _closed(
                {
                    "artifact_digest": _ref("sha256"),
                    "canonical_path": {
                        "const": CONTROL_INTERFACE_PATH
                    },
                    "digest_basis": {"const": "RAW_BYTES"},
                    "source_git_object_id": _ref("git_object_id"),
                    "unchanged": {"const": True},
                }
            ),
            "promotion_to_candidate_performed": {"const": False},
            "release_write_permitted": {"const": False},
            "version_file_created": {"const": False},
        }
    )
    schema: Dict[str, Any] = {
        "$id": VERSION_POLICY_CONSUMER_READINESS_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Mechanism version-policy v3 consumer-first readiness",
        **_closed(
            {
                "artifact_digest": _ref("sha256"),
                "canonicalization": canonicalization,
                "compatibility": compatibility,
                "consumer_contract": consumer_contract,
                "consumer_inventory": {
                    "items": consumer_item,
                    "maxItems": 6,
                    "minItems": 6,
                    "type": "array",
                    "uniqueItems": True,
                },
                "digest_algorithm": {"const": "SHA-256"},
                "next_phase": {"const": NEXT_PHASE},
                "nonmutation": nonmutation,
                "owner_plane": {"const": "MECHANISM"},
                "protocol_revision": _ref("protocol_revision"),
                "schedule": schedule,
                "schema_version": {
                    "const": VERSION_POLICY_CONSUMER_READINESS_SCHEMA_ID
                },
                "self_digest_pointer": {"const": "/artifact_digest"},
                "source_trust": source_trust,
                "status": {
                    "const": (
                        "DRAFT_NON_ACTIVE_MECHANISM_CONSUMER_READY"
                    )
                },
                "task_pack_revision": {"const": TASK_PACK_REVISION},
            }
        ),
    }
    return schema


def _consumer_inventory() -> list[Mapping[str, Any]]:
    rows = []
    for component_id, relative_path, observed_support in (
        MECHANISM_CONSUMER_PATHS
    ):
        raw = REPO_ROOT.joinpath(*relative_path.split("/")).read_bytes()
        rows.append(
            {
                "component_id": component_id,
                "content_digest": _sha256(raw),
                "observed_support": observed_support,
                "owner_plane": "MECHANISM",
                "relative_path": relative_path,
                "required_action": "NONE",
                "source_binding_mode": (
                    "SUCCESSOR_EXTERNAL_TUPLE_REQUIRED"
                ),
                "source_git_object_id": None,
            }
        )
    for component_id, relative_path, observed_support in AUTO_CONSUMER_PATHS:
        raw = _git_blob(AUTO_GIT_OBJECT, relative_path)
        local = REPO_ROOT.joinpath(*relative_path.split("/")).read_bytes()
        if raw != local:
            raise VersionPolicyConsumerReadinessBuildError(
                "VERSION_POLICY_CONSUMER_READINESS_AUTO_LOCAL_DRIFT:"
                + relative_path
            )
        rows.append(
            {
                "component_id": component_id,
                "content_digest": _sha256(raw),
                "observed_support": observed_support,
                "owner_plane": "AUTO",
                "relative_path": relative_path,
                "required_action": "AUTO_DUAL_READ_INTEGRATION",
                "source_binding_mode": "IMMUTABLE_GIT_OBJECT",
                "source_git_object_id": AUTO_GIT_OBJECT,
            }
        )
    rows.sort(key=lambda row: row["component_id"])
    return rows


def build_interface() -> Mapping[str, Any]:
    candidate_trust = TrustTuple(
        verified_git_object_id=CANDIDATE_GIT_OBJECT,
        expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
        canonical_manifest_path=CANDIDATE_MANIFEST_PATH,
        mode="CANDIDATE",
    )
    draft_trust = VersionPolicyDraftTrustTuple(
        verified_git_object_id=DRAFT_GIT_OBJECT,
        expected_interface_raw_sha256=DRAFT_INTERFACE_RAW_SHA256,
        canonical_interface_path=DRAFT_INTERFACE_PATH,
        mode=DRAFT_INTERFACE_MODE,
    )
    trusted = load_trusted_version_policies(
        REPO_ROOT,
        candidate_trust,
        CANDIDATE_MANIFEST_RAW_SHA256,
        draft_trust,
    )
    if (
        trusted.candidate_manifest_raw_sha256
        != CANDIDATE_MANIFEST_RAW_SHA256
        or trusted.draft_interface_raw_sha256
        != DRAFT_INTERFACE_RAW_SHA256
    ):
        raise VersionPolicyConsumerReadinessBuildError(
            "VERSION_POLICY_CONSUMER_READINESS_TRUST_DIGEST_MISMATCH"
        )
    auto_interface_raw = _git_blob(
        AUTO_GIT_OBJECT,
        AUTO_RUNTIME_INTERFACE_PATH,
    )
    if (
        _sha256(auto_interface_raw) != AUTO_RUNTIME_INTERFACE_RAW_SHA256
        or auto_interface_raw
        != REPO_ROOT.joinpath(
            *AUTO_RUNTIME_INTERFACE_PATH.split("/")
        ).read_bytes()
    ):
        raise VersionPolicyConsumerReadinessBuildError(
            "VERSION_POLICY_CONSUMER_READINESS_AUTO_INTERFACE_DRIFT"
        )
    control_raw = REPO_ROOT.joinpath(
        *CONTROL_INTERFACE_PATH.split("/")
    ).read_bytes()
    if (
        _sha256(control_raw) != CONTROL_INTERFACE_RAW_SHA256
        or control_raw
        != _git_blob(DRAFT_GIT_OBJECT, CONTROL_INTERFACE_PATH)
    ):
        raise VersionPolicyConsumerReadinessBuildError(
            "VERSION_POLICY_CONSUMER_READINESS_CONTROL_DRIFT"
        )
    if ACTIVE_VERSION_PATH.exists():
        raise VersionPolicyConsumerReadinessBuildError(
            "VERSION_POLICY_CONSUMER_READINESS_ACTIVE_VERSION_FORBIDDEN"
        )
    compatibility = {
        **trusted.compatibility,
        "mechanism_consumer_first_verified": True,
        "auto_consumer_first_verified": False,
        "cross_plane_consumer_first_complete": False,
        "candidate_materialization_permitted": False,
    }
    interface: Dict[str, Any] = {
        "schema_version": VERSION_POLICY_CONSUMER_READINESS_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "owner_plane": "MECHANISM",
        "status": "DRAFT_NON_ACTIVE_MECHANISM_CONSUMER_READY",
        "task_pack_revision": TASK_PACK_REVISION,
        "canonicalization": {
            "duplicate_keys": "REJECT",
            "encoding": "UTF-8",
            "input_profile": "I_JSON",
            "scheme": "RFC8785_JCS",
            "self_digest_exclusion": (
                "EXACT_DECLARED_JSON_POINTER_ONLY"
            ),
            "unicode_normalization": "NONE",
        },
        "digest_algorithm": "SHA-256",
        "self_digest_pointer": "/artifact_digest",
        "source_trust": {
            "predecessor_candidate": {
                "verified_git_object_id": CANDIDATE_GIT_OBJECT,
                "canonical_path": CANDIDATE_MANIFEST_PATH,
                "expected_mode": "CANDIDATE",
                "artifact_digest": CANDIDATE_MANIFEST_RAW_SHA256,
                "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
                "schema_count": 31,
                "policy_count": 5,
            },
            "v3_draft": {
                "verified_git_object_id": DRAFT_GIT_OBJECT,
                "canonical_path": DRAFT_INTERFACE_PATH,
                "expected_mode": DRAFT_INTERFACE_MODE,
                "artifact_digest": DRAFT_INTERFACE_RAW_SHA256,
            },
            "repository_self_report_is_not_trust_root": True,
        },
        "consumer_contract": {
            "accepted_policy_ids": [
                VERSION_POLICY_V2_ID,
                VERSION_POLICY_V3_ID,
            ],
            "selection_mode_required": True,
            "predecessor_selection_mode": PREDECESSOR_SELECTION_MODE,
            "successor_selection_mode": SUCCESSOR_SELECTION_MODE,
            "hybrid_selection_forbidden": True,
            "unknown_policy_id_action": "FAIL_CLOSED",
            "unknown_or_duplicate_trigger_action": "FAIL_CLOSED",
            "stronger_impact_downgrade_allowed": False,
            "mechanism_dual_read_verified": True,
            "mechanism_schedule_fail_closed_verified": True,
            "auto_dual_read_verified": False,
            "cross_plane_consumer_first_complete": False,
        },
        "compatibility": compatibility,
        "consumer_inventory": _consumer_inventory(),
        "schedule": {
            "timezone": "Australia/Sydney",
            "authority_state": "UNRESOLVED",
            "candidate_local_times": list(SCHEDULE_CANDIDATES),
            "selected_local_time": None,
            "conflict_code": UNRESOLVED_SCHEDULE_CODE,
            "activation_permitted": False,
        },
        "nonmutation": {
            "candidate_bundle_unchanged": True,
            "control_interface": {
                "source_git_object_id": DRAFT_GIT_OBJECT,
                "canonical_path": CONTROL_INTERFACE_PATH,
                "digest_basis": "RAW_BYTES",
                "artifact_digest": CONTROL_INTERFACE_RAW_SHA256,
                "unchanged": True,
            },
            "promotion_to_candidate_performed": False,
            "release_write_permitted": False,
            "canonical_publication_permitted": False,
            "activation_forbidden": True,
            "version_file_created": False,
        },
        "next_phase": NEXT_PHASE,
        "artifact_digest": "0" * 64,
    }
    interface["artifact_digest"] = canonical_digest(
        interface,
        "/artifact_digest",
    )
    return interface


def render_schema() -> bytes:
    return _render(build_schema())


def render_interface() -> bytes:
    return _render(build_interface())


def validate_interface(interface: Mapping[str, Any]) -> None:
    expected = build_interface()
    if interface != expected:
        raise VersionPolicyConsumerReadinessBuildError(
            "VERSION_POLICY_CONSUMER_READINESS_SEMANTIC_DRIFT"
        )
    if interface["artifact_digest"] != canonical_digest(
        interface,
        "/artifact_digest",
    ):
        raise VersionPolicyConsumerReadinessBuildError(
            "VERSION_POLICY_CONSUMER_READINESS_SELF_DIGEST_MISMATCH"
        )
    common_schema = _load(
        GOVERNANCE_DIR / "schemas" / "common-definitions.schema.json"
    )
    schema = build_schema()
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource

    registry = Registry().with_resources(
        (
            (common_schema["$id"], Resource.from_contents(common_schema)),
            (schema["$id"], Resource.from_contents(schema)),
        )
    )
    errors = list(
        Draft202012Validator(
            schema,
            registry=registry,
        ).iter_errors(interface)
    )
    if errors:
        raise VersionPolicyConsumerReadinessBuildError(
            "VERSION_POLICY_CONSUMER_READINESS_SCHEMA_INVALID"
        )
    trusted = load_trusted_version_policies(
        REPO_ROOT,
        TrustTuple(
            verified_git_object_id=CANDIDATE_GIT_OBJECT,
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            canonical_manifest_path=CANDIDATE_MANIFEST_PATH,
            mode="CANDIDATE",
        ),
        CANDIDATE_MANIFEST_RAW_SHA256,
        VersionPolicyDraftTrustTuple(
            verified_git_object_id=DRAFT_GIT_OBJECT,
            expected_interface_raw_sha256=DRAFT_INTERFACE_RAW_SHA256,
            canonical_interface_path=DRAFT_INTERFACE_PATH,
            mode=DRAFT_INTERFACE_MODE,
        ),
    )
    scan_public_value(interface, trusted.candidate_bundle.policies)


def _check() -> None:
    if SCHEMA_PATH.read_bytes() != render_schema():
        raise VersionPolicyConsumerReadinessBuildError(
            "VERSION_POLICY_CONSUMER_READINESS_SCHEMA_NOT_BYTE_EQUIVALENT"
        )
    if OUTPUT_PATH.read_bytes() != render_interface():
        raise VersionPolicyConsumerReadinessBuildError(
            "VERSION_POLICY_CONSUMER_READINESS_NOT_BYTE_EQUIVALENT"
        )
    interface = _load(OUTPUT_PATH)
    validate_interface(interface)
    print(
        "VERSION_POLICY_V3_CONSUMER_READINESS_BYTE_EQUIVALENT "
        "mechanism_dual_read=true auto_dual_read=false "
        "cross_plane_complete=false schedule=UNRESOLVED "
        f"next_phase={interface['next_phase']} "
        f"artifact_digest={interface['artifact_digest']} "
        f"schema_sha256={_canonical_sha(build_schema())}"
    )


def _write() -> None:
    SCHEMA_PATH.write_bytes(render_schema())
    OUTPUT_PATH.write_bytes(render_interface())
    _check()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--print-interface", action="store_true")
    mode.add_argument("--print-schema", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        _check()
    elif args.write:
        _write()
    elif args.print_interface:
        sys.stdout.buffer.write(render_interface())
    else:
        sys.stdout.buffer.write(render_schema())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        ValueError,
        VersionPolicyConsumerReadinessBuildError,
    ) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
