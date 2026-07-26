"""Semantic gates for the non-active SkillOps version-policy v3 draft."""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence, Tuple

from CodexSkills.governance.release.foundations import (
    LOCKED_MAJOR_TRIGGER_CODES,
    MATERIAL_TRIGGER_CODES,
    ROUTINE_TRIGGER_CODES,
    validate_version_policy,
)


PROTOCOL_REVISION = (
    "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
)
VERSION_POLICY_V3_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:version-policy:v3"
)
VERSION_POLICY_V3_ID = (
    "urn:linzecolin:agentdatabase:skillops:policy:version:v3"
)
VERSION_POLICY_DRAFT_INTERFACE_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:version-policy-draft-interface:v1"
)
VERSION_POLICY_V2_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:version-policy:v2"
)
VERSION_POLICY_V2_ID = (
    "urn:linzecolin:agentdatabase:skillops:policy:version:v2"
)
NOTIFICATION_POLICY_ID = (
    "urn:linzecolin:agentdatabase:skillops:policy:notification:v1"
)

TASK_PACK_REVISION = "v0.0.0.2"
SRV_PATTERN = r"^v0\.0\.0\.[1-9][0-9]*$"
SCHEDULE_TIME_RE = re.compile(
    r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$"
)
UNRESOLVED_SCHEDULE_CODE = (
    "OWNER_AUTHORITY_0415_VS_GOAL_0530_UNRESOLVED"
)
SCHEDULE_CANDIDATES = ("04:15", "05:30")
IMPACT_TRANSLATION = {
    "ROUTINE": "PATCH",
    "MATERIAL": "MINOR",
    "MAJOR": "MAJOR",
}
V2_MISSING_MAJOR_TRIGGER_CODES = tuple(
    sorted(
        {
            "AUTOMATIC_SIDE_EFFECT_CHANGE",
            "EVALUATOR_OR_HOLDOUT_CHANGE",
            "HARD_GATE_CHANGE",
            "MIGRATION_OR_DELETE_SEMANTICS_CHANGE",
            "NETWORK_OR_PERMISSION_CHANGE",
            "PRIVACY_POLICY_CHANGE",
        }
    )
)

POLICY_KEYS = frozenset(
    {
        "schema_version",
        "protocol_revision",
        "policy_id",
        "task_pack_revision",
        "scheme_name",
        "semver_compatible",
        "srv_pattern",
        "canonical_counter_path",
        "bootstrap_if_missing",
        "srv_release_scopes",
        "srv_update_mode",
        "srv_reuse_allowed",
        "srv_last_component_bounded",
        "independent_subsystem_counters",
        "transaction_semantics",
        "daily_run_increments_srv",
        "srv_revision_used_as_daily_sequence",
        "daily_transaction_uid_separate",
        "daily_transaction_uid_kind",
        "impact_levels",
        "impact_translation",
        "routine_trigger_codes",
        "material_trigger_codes",
        "major_trigger_codes",
        "unknown_trigger_action",
        "impact_downgrade_allowed",
        "policy_conflict_action",
        "policy_repair_requires_srv_increment",
        "sensitive_policy_repair_impact",
        "notification_policy_id",
        "major_notification_required",
        "planned_major_provider_sent_before_write",
        "planned_major_write_without_sent_allowed",
        "owner_approval_required",
        "owner_reply_required",
        "emergency_containment_precedes_notification",
        "actual_recipient_mapping_repo_external",
        "timezone",
        "daily_schedule_authority_state",
        "daily_schedule_local",
        "daily_schedule_candidate_local_times",
        "schedule_conflict_code",
        "schedule_activation_permitted",
        "sunday_forced_full",
        "late_start_rejected",
        "manual_uses_same_orchestrator",
        "first_active_requires_exact_bundle_digest",
    }
)


class VersionPolicyV3Error(ValueError):
    """The version-policy v3 draft violates a frozen invariant."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _exact(value: Any, expected: Any, code: str) -> None:
    if value != expected or type(value) is not type(expected):
        raise VersionPolicyV3Error(code)


def _exact_sorted_codes(
    value: Any,
    expected: Sequence[str],
    code: str,
) -> Tuple[str, ...]:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) for item in value)
        or value != sorted(set(value))
        or tuple(value) != tuple(sorted(expected))
    ):
        raise VersionPolicyV3Error(code)
    return tuple(value)


def validate_version_policy_v3(
    policy: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Validate current or future-resolved v3 instances without guessing time."""

    if not isinstance(policy, dict) or set(policy) != POLICY_KEYS:
        raise VersionPolicyV3Error("VERSION_POLICY_V3_SHAPE_INVALID")
    exact_values = {
        "schema_version": VERSION_POLICY_V3_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "policy_id": VERSION_POLICY_V3_ID,
        "task_pack_revision": TASK_PACK_REVISION,
        "scheme_name": "SKILLOPS_REVISION_VERSION",
        "semver_compatible": False,
        "srv_pattern": SRV_PATTERN,
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
        "impact_translation": IMPACT_TRANSLATION,
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
        "daily_schedule_candidate_local_times": list(
            SCHEDULE_CANDIDATES
        ),
        "sunday_forced_full": True,
        "late_start_rejected": False,
        "manual_uses_same_orchestrator": True,
        "first_active_requires_exact_bundle_digest": True,
    }
    for field, expected in exact_values.items():
        _exact(
            policy[field],
            expected,
            "VERSION_POLICY_V3_FIELD_MISMATCH:" + field,
        )

    routine = _exact_sorted_codes(
        policy["routine_trigger_codes"],
        ROUTINE_TRIGGER_CODES,
        "VERSION_POLICY_V3_ROUTINE_TRIGGER_SET_INVALID",
    )
    material = _exact_sorted_codes(
        policy["material_trigger_codes"],
        MATERIAL_TRIGGER_CODES,
        "VERSION_POLICY_V3_MATERIAL_TRIGGER_SET_INVALID",
    )
    major = _exact_sorted_codes(
        policy["major_trigger_codes"],
        LOCKED_MAJOR_TRIGGER_CODES,
        "VERSION_POLICY_V3_MAJOR_TRIGGER_SET_INVALID",
    )
    if set(routine).intersection(material, major) or set(material).intersection(
        major
    ):
        raise VersionPolicyV3Error(
            "VERSION_POLICY_V3_TRIGGER_SETS_OVERLAP"
        )

    authority_state = policy["daily_schedule_authority_state"]
    if authority_state == "UNRESOLVED":
        if (
            policy["daily_schedule_local"] is not None
            or policy["schedule_conflict_code"]
            != UNRESOLVED_SCHEDULE_CODE
            or policy["schedule_activation_permitted"] is not False
        ):
            raise VersionPolicyV3Error(
                "VERSION_POLICY_V3_UNRESOLVED_SCHEDULE_INVALID"
            )
    elif authority_state == "RESOLVED":
        selected = policy["daily_schedule_local"]
        if (
            not isinstance(selected, str)
            or not SCHEDULE_TIME_RE.fullmatch(selected)
            or selected not in SCHEDULE_CANDIDATES
            or policy["schedule_conflict_code"] is not None
            or policy["schedule_activation_permitted"] is not True
        ):
            raise VersionPolicyV3Error(
                "VERSION_POLICY_V3_RESOLVED_SCHEDULE_INVALID"
            )
    else:
        raise VersionPolicyV3Error(
            "VERSION_POLICY_V3_SCHEDULE_AUTHORITY_STATE_INVALID"
        )
    return policy


def classify_v3_impact(
    trigger_codes: Sequence[str],
    policy: Mapping[str, Any],
) -> str:
    """Return the strongest locked impact; unknown or duplicate codes stop."""

    validate_version_policy_v3(policy)
    if (
        not isinstance(trigger_codes, (list, tuple))
        or not trigger_codes
        or any(not isinstance(code, str) for code in trigger_codes)
    ):
        raise VersionPolicyV3Error(
            "VERSION_POLICY_V3_TRIGGER_INPUT_INVALID"
        )
    normalized = tuple(sorted(trigger_codes))
    if len(set(normalized)) != len(normalized):
        raise VersionPolicyV3Error(
            "VERSION_POLICY_V3_TRIGGER_DUPLICATE"
        )
    routine = set(policy["routine_trigger_codes"])
    material = set(policy["material_trigger_codes"])
    major = set(policy["major_trigger_codes"])
    unknown = set(normalized).difference(routine, material, major)
    if unknown:
        raise VersionPolicyV3Error(
            "VERSION_POLICY_V3_TRIGGER_UNKNOWN"
        )
    if set(normalized).intersection(major):
        return "MAJOR"
    if set(normalized).intersection(material):
        return "MINOR"
    return "PATCH"


def assert_schedule_activation_permitted(
    policy: Mapping[str, Any],
) -> None:
    validate_version_policy_v3(policy)
    if policy["schedule_activation_permitted"] is not True:
        raise VersionPolicyV3Error(
            "VERSION_POLICY_V3_SCHEDULE_AUTHORITY_UNRESOLVED"
        )


def validate_v2_to_v3_compatibility(
    predecessor: Mapping[str, Any],
    successor: Mapping[str, Any],
    notification_policy: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Prove exact trigger closure while retaining fail-closed consumer order."""

    if (
        predecessor.get("schema_version") != VERSION_POLICY_V2_SCHEMA_ID
        or predecessor.get("policy_id") != VERSION_POLICY_V2_ID
    ):
        raise VersionPolicyV3Error(
            "VERSION_POLICY_V3_PREDECESSOR_IDENTITY_INVALID"
        )
    try:
        missing = validate_version_policy(predecessor)
    except ValueError as exc:
        raise VersionPolicyV3Error(
            "VERSION_POLICY_V3_PREDECESSOR_INVALID"
        ) from exc
    validate_version_policy_v3(successor)
    if tuple(missing) != V2_MISSING_MAJOR_TRIGGER_CODES:
        raise VersionPolicyV3Error(
            "VERSION_POLICY_V3_PREDECESSOR_GAP_MISMATCH"
        )
    predecessor_major = set(predecessor["major_trigger_codes"])
    successor_major = set(successor["major_trigger_codes"])
    if (
        not predecessor_major.issubset(successor_major)
        or tuple(sorted(successor_major - predecessor_major))
        != V2_MISSING_MAJOR_TRIGGER_CODES
    ):
        raise VersionPolicyV3Error(
            "VERSION_POLICY_V3_MAJOR_TRIGGER_CLOSURE_INVALID"
        )
    preserved = {
        "srv_pattern": "srv_pattern",
        "srv_release_scopes": "srv_release_scopes",
        "srv_update_mode": "srv_update_mode",
        "srv_reuse_allowed": "srv_reuse_allowed",
        "srv_last_component_bounded": "srv_last_component_bounded",
        "daily_transaction_uid_separate": (
            "daily_transaction_uid_separate"
        ),
        "timezone": "timezone",
        "sunday_forced_full": "sunday_forced_full",
        "late_start_rejected": "late_start_rejected",
        "manual_uses_same_orchestrator": (
            "manual_uses_same_orchestrator"
        ),
        "first_active_requires_exact_bundle_digest": (
            "first_active_requires_exact_bundle_digest"
        ),
    }
    for old_field, new_field in preserved.items():
        if predecessor[old_field] != successor[new_field]:
            raise VersionPolicyV3Error(
                "VERSION_POLICY_V3_PREDECESSOR_INVARIANT_DRIFT:"
                + old_field
            )
    if (
        predecessor["transaction_uid_kind"]
        != successor["daily_transaction_uid_kind"]
        or predecessor["daily_schedule_local"]
        not in successor["daily_schedule_candidate_local_times"]
    ):
        raise VersionPolicyV3Error(
            "VERSION_POLICY_V3_PREDECESSOR_CONTEXT_DRIFT"
        )
    expected_notification = {
        "policy_id": NOTIFICATION_POLICY_ID,
        "automatic": True,
        "notification_only": True,
        "owner_reply_required": False,
        "owner_approval_required": False,
        "planned_major_provider_sent_before_write": True,
        "send_failure_blocks_planned_write": True,
        "emergency_containment_precedes_notification": True,
        "actual_recipient_mapping_repo_external": True,
    }
    if not isinstance(notification_policy, dict) or any(
        notification_policy.get(field) != expected
        for field, expected in expected_notification.items()
    ):
        raise VersionPolicyV3Error(
            "VERSION_POLICY_V3_NOTIFICATION_PREDECESSOR_INVALID"
        )
    if (
        successor["notification_policy_id"]
        != notification_policy["policy_id"]
        or successor["planned_major_provider_sent_before_write"]
        is not True
        or successor["planned_major_write_without_sent_allowed"]
        is not False
        or successor["owner_reply_required"]
        != notification_policy["owner_reply_required"]
        or successor["owner_approval_required"]
        != notification_policy["owner_approval_required"]
        or successor["emergency_containment_precedes_notification"]
        != notification_policy[
            "emergency_containment_precedes_notification"
        ]
        or successor["actual_recipient_mapping_repo_external"]
        != notification_policy[
            "actual_recipient_mapping_repo_external"
        ]
    ):
        raise VersionPolicyV3Error(
            "VERSION_POLICY_V3_NOTIFICATION_SEMANTICS_DRIFT"
        )
    return {
        "compatibility_mode": "CONSUMER_FIRST_REPLACEMENT",
        "change_class": "MAJOR",
        "predecessor_policy_accepted": True,
        "existing_v2_major_trigger_codes_preserved": True,
        "missing_major_trigger_codes_closed": list(missing),
        "daily_srv_separation_explicit": True,
        "notification_semantics_preserved": True,
        "schedule_authority_resolved": (
            successor["daily_schedule_authority_state"] == "RESOLVED"
        ),
    }
