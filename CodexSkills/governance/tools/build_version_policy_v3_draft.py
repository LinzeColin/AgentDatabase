#!/usr/bin/env python3
"""Build/check the non-active version-policy v3 consumer-first draft."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from CodexSkills.governance.release.foundations import (  # noqa: E402
    LOCKED_MAJOR_TRIGGER_CODES,
    MATERIAL_TRIGGER_CODES,
    ROUTINE_TRIGGER_CODES,
)
from CodexSkills.governance.release.version_policy_v3.contract import (  # noqa: E402
    IMPACT_TRANSLATION,
    NOTIFICATION_POLICY_ID,
    PROTOCOL_REVISION,
    SCHEDULE_CANDIDATES,
    TASK_PACK_REVISION,
    UNRESOLVED_SCHEDULE_CODE,
    VERSION_POLICY_DRAFT_INTERFACE_SCHEMA_ID,
    VERSION_POLICY_V3_ID,
    VERSION_POLICY_V3_SCHEMA_ID,
    validate_v2_to_v3_compatibility,
    validate_version_policy_v3,
)
from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
)


GOVERNANCE_DIR = REPO_ROOT / "CodexSkills" / "governance"
DRAFT_DIR = GOVERNANCE_DIR / "release" / "version_policy_v3"
POLICY_PATH = DRAFT_DIR / "version-policy.v3.json"
POLICY_SCHEMA_PATH = DRAFT_DIR / "schemas" / "version-policy.schema.json"
INTERFACE_PATH = DRAFT_DIR / "draft-interface.json"
INTERFACE_SCHEMA_PATH = (
    DRAFT_DIR / "schemas" / "draft-interface.schema.json"
)
PREDECESSOR_POLICY_PATH = (
    GOVERNANCE_DIR / "policies" / "version-policy.v2.json"
)
PREDECESSOR_SCHEMA_PATH = (
    GOVERNANCE_DIR / "schemas" / "version-policy.schema.json"
)
NOTIFICATION_POLICY_PATH = (
    GOVERNANCE_DIR / "policies" / "notification-policy.v1.json"
)
FOUNDATION_INTERFACE_PATH = (
    GOVERNANCE_DIR / "release" / "foundation-interface.json"
)
CANDIDATE_MANIFEST_PATH = (
    GOVERNANCE_DIR / "bundles" / "schema-bundle-manifest.v1.json"
)
CONTROL_INTERFACE_PATH = (
    GOVERNANCE_DIR / "activation" / "control-interface.json"
)
ACTIVE_VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"
NEXT_PHASE = "MECHANISM_VERSION_POLICY_V3_CONSUMER_FIRST_READINESS"


class VersionPolicyV3BuildError(ValueError):
    """The v3 draft cannot be reproduced or safely staged."""


def _load(path: Path) -> Mapping[str, Any]:
    try:
        value = parse_json_bytes(path.read_bytes())
    except Exception as exc:
        raise VersionPolicyV3BuildError(
            "VERSION_POLICY_V3_JSON_INVALID:" + path.as_posix()
        ) from exc
    if not isinstance(value, dict):
        raise VersionPolicyV3BuildError(
            "VERSION_POLICY_V3_JSON_ROOT_INVALID:" + path.as_posix()
        )
    return value


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_sha(value: Mapping[str, Any]) -> str:
    return _sha256(canonicalize_object(value))


def build_policy() -> Mapping[str, Any]:
    policy: Dict[str, Any] = {
        "schema_version": VERSION_POLICY_V3_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "policy_id": VERSION_POLICY_V3_ID,
        "task_pack_revision": TASK_PACK_REVISION,
        "scheme_name": "SKILLOPS_REVISION_VERSION",
        "semver_compatible": False,
        "srv_pattern": r"^v0\.0\.0\.[1-9][0-9]*$",
        "canonical_counter_path": "CodexSkills/VERSION",
        "bootstrap_if_missing": "v0.0.0.2",
        "srv_release_scopes": [
            "MECHANISM",
            "SCHEMA",
            "POLICY",
            "REGISTRY",
        ],
        "srv_update_mode": "GLOBAL_ATOMIC_INCREMENT",
        "srv_reuse_allowed": False,
        "srv_last_component_bounded": False,
        "independent_subsystem_counters": False,
        "transaction_semantics": (
            "ONE_SRV_PER_ACCEPTED_CANONICAL_TRANSACTION"
        ),
        "daily_run_increments_srv": False,
        "srv_revision_used_as_daily_sequence": False,
        "daily_transaction_uid_separate": True,
        "daily_transaction_uid_kind": "AUTO_TRANSACTION_UID",
        "impact_levels": ["PATCH", "MINOR", "MAJOR"],
        "impact_translation": dict(IMPACT_TRANSLATION),
        "routine_trigger_codes": sorted(ROUTINE_TRIGGER_CODES),
        "material_trigger_codes": sorted(MATERIAL_TRIGGER_CODES),
        "major_trigger_codes": sorted(LOCKED_MAJOR_TRIGGER_CODES),
        "unknown_trigger_action": "FAIL_CLOSED",
        "impact_downgrade_allowed": False,
        "policy_conflict_action": "STOP_WRITE",
        "policy_repair_requires_srv_increment": True,
        "sensitive_policy_repair_impact": "MAJOR",
        "notification_policy_id": NOTIFICATION_POLICY_ID,
        "major_notification_required": True,
        "planned_major_provider_sent_before_write": True,
        "planned_major_write_without_sent_allowed": False,
        "owner_approval_required": False,
        "owner_reply_required": False,
        "emergency_containment_precedes_notification": True,
        "actual_recipient_mapping_repo_external": True,
        "timezone": "Australia/Sydney",
        "daily_schedule_authority_state": "UNRESOLVED",
        "daily_schedule_local": None,
        "daily_schedule_candidate_local_times": list(
            SCHEDULE_CANDIDATES
        ),
        "schedule_conflict_code": UNRESOLVED_SCHEDULE_CODE,
        "schedule_activation_permitted": False,
        "sunday_forced_full": True,
        "late_start_rejected": False,
        "manual_uses_same_orchestrator": True,
        "first_active_requires_exact_bundle_digest": True,
    }
    return validate_version_policy_v3(policy)


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


def render_policy() -> bytes:
    return _render(build_policy())


def build_interface() -> Mapping[str, Any]:
    predecessor = _load(PREDECESSOR_POLICY_PATH)
    notification_policy = _load(NOTIFICATION_POLICY_PATH)
    policy = build_policy()
    compatibility = dict(
        validate_v2_to_v3_compatibility(
            predecessor,
            policy,
            notification_policy,
        )
    )
    compatibility.update(
        {
            "consumer_first_verified": False,
            "candidate_materialization_permitted": False,
        }
    )
    foundation = _load(FOUNDATION_INTERFACE_PATH)
    if foundation.get("artifact_digest") != canonical_digest(
        foundation,
        "/artifact_digest",
    ):
        raise VersionPolicyV3BuildError(
            "VERSION_POLICY_V3_FOUNDATION_DIGEST_INVALID"
        )
    candidate = _load(CANDIDATE_MANIFEST_PATH)
    candidate_schema_ids = {row["id"] for row in candidate["schemas"]}
    candidate_policy_ids = {row["id"] for row in candidate["policies"]}
    if (
        VERSION_POLICY_V3_SCHEMA_ID in candidate_schema_ids
        or VERSION_POLICY_V3_ID in candidate_policy_ids
    ):
        raise VersionPolicyV3BuildError(
            "VERSION_POLICY_V3_PREMATURE_CANDIDATE_MEMBERSHIP"
        )
    interface: Dict[str, Any] = {
        "schema_version": VERSION_POLICY_DRAFT_INTERFACE_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "status": "DRAFT_NON_ACTIVE_CONSUMER_FIRST_REQUIRED",
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
        "draft_trust_contract": {
            "canonical_path": (
                "CodexSkills/governance/release/version_policy_v3/"
                "draft-interface.json"
            ),
            "expected_mode": "DRAFT_NON_ACTIVE_VERSION_POLICY",
            "external_expected_raw_sha256_required": True,
            "external_verified_git_object_required": True,
            "repository_self_report_is_not_trust_root": True,
        },
        "foundation_interface": {
            "relative_path": (
                "CodexSkills/governance/release/"
                "foundation-interface.json"
            ),
            "artifact_digest": foundation["artifact_digest"],
        },
        "interface_schema": {
            "schema_id": VERSION_POLICY_DRAFT_INTERFACE_SCHEMA_ID,
            "relative_path": (
                "CodexSkills/governance/release/version_policy_v3/"
                "schemas/draft-interface.schema.json"
            ),
            "schema_sha256": _canonical_sha(
                _load(INTERFACE_SCHEMA_PATH)
            ),
        },
        "predecessor": {
            "schema_id": predecessor["schema_version"],
            "schema_path": (
                "CodexSkills/governance/schemas/"
                "version-policy.schema.json"
            ),
            "schema_sha256": _canonical_sha(
                _load(PREDECESSOR_SCHEMA_PATH)
            ),
            "policy_id": predecessor["policy_id"],
            "policy_path": (
                "CodexSkills/governance/policies/"
                "version-policy.v2.json"
            ),
            "policy_sha256": _canonical_sha(predecessor),
        },
        "draft": {
            "schema_id": VERSION_POLICY_V3_SCHEMA_ID,
            "schema_path": (
                "CodexSkills/governance/release/version_policy_v3/"
                "schemas/version-policy.schema.json"
            ),
            "schema_sha256": _canonical_sha(
                _load(POLICY_SCHEMA_PATH)
            ),
            "policy_id": VERSION_POLICY_V3_ID,
            "policy_path": (
                "CodexSkills/governance/release/version_policy_v3/"
                "version-policy.v3.json"
            ),
            "policy_sha256": _canonical_sha(policy),
        },
        "notification_policy": {
            "policy_id": notification_policy["policy_id"],
            "relative_path": (
                "CodexSkills/governance/policies/"
                "notification-policy.v1.json"
            ),
            "policy_sha256": _canonical_sha(notification_policy),
        },
        "compatibility": compatibility,
        "candidate_bundle": {
            "bundle_digest": candidate["bundle_digest"],
            "schema_count": candidate["schema_count"],
            "policy_count": candidate["policy_count"],
            "v3_schema_member": False,
            "v3_policy_member": False,
            "unchanged": True,
        },
        "control_interface": {
            "relative_path": (
                "CodexSkills/governance/activation/"
                "control-interface.json"
            ),
            "digest_basis": "RAW_BYTES",
            "artifact_digest": _sha256(
                CONTROL_INTERFACE_PATH.read_bytes()
            ),
            "unchanged": True,
        },
        "schedule_authority_resolved": False,
        "release_write_permitted": False,
        "canonical_publication_permitted": False,
        "activation_forbidden": True,
        "promotion_to_candidate_performed": False,
        "version_file_created": False,
        "next_phase": NEXT_PHASE,
        "artifact_digest": "0" * 64,
    }
    interface["artifact_digest"] = canonical_digest(
        interface,
        "/artifact_digest",
    )
    return interface


def render_interface() -> bytes:
    return _render(build_interface())


def validate_interface(interface: Mapping[str, Any]) -> None:
    if interface != build_interface():
        raise VersionPolicyV3BuildError(
            "VERSION_POLICY_V3_INTERFACE_SEMANTIC_DRIFT"
        )
    if interface["artifact_digest"] != canonical_digest(
        interface,
        "/artifact_digest",
    ):
        raise VersionPolicyV3BuildError(
            "VERSION_POLICY_V3_INTERFACE_DIGEST_MISMATCH"
        )
    if ACTIVE_VERSION_PATH.exists():
        raise VersionPolicyV3BuildError(
            "VERSION_POLICY_V3_ACTIVE_VERSION_FORBIDDEN"
        )


def _check() -> None:
    if POLICY_PATH.read_bytes() != render_policy():
        raise VersionPolicyV3BuildError(
            "VERSION_POLICY_V3_POLICY_NOT_BYTE_EQUIVALENT"
        )
    if INTERFACE_PATH.read_bytes() != render_interface():
        raise VersionPolicyV3BuildError(
            "VERSION_POLICY_V3_INTERFACE_NOT_BYTE_EQUIVALENT"
        )
    policy = _load(POLICY_PATH)
    validate_version_policy_v3(policy)
    interface = _load(INTERFACE_PATH)
    validate_interface(interface)
    print(
        "VERSION_POLICY_V3_DRAFT_BYTE_EQUIVALENT "
        f"major_triggers={len(policy['major_trigger_codes'])} "
        "schedule=UNRESOLVED candidate_membership=false "
        f"next_phase={interface['next_phase']} "
        f"artifact_digest={interface['artifact_digest']}"
    )


def _write() -> None:
    policy_raw = render_policy()
    interface_raw = render_interface()
    POLICY_PATH.write_bytes(policy_raw)
    INTERFACE_PATH.write_bytes(interface_raw)
    _check()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--print-policy", action="store_true")
    mode.add_argument("--print-interface", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        _check()
    elif args.write:
        _write()
    elif args.print_policy:
        sys.stdout.buffer.write(render_policy())
    else:
        sys.stdout.buffer.write(render_interface())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, VersionPolicyV3BuildError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
