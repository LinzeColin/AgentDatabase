#!/usr/bin/env python3
"""Mechanism-owned semantic consumer for public-run-event:v2.

The shared schema remains Auto-owned. This module owns the consumer-side
cross-field checks without importing Auto runtime code or changing the pinned
M0c-A activation runtime bytes.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Mapping

from canonical_json import canonicalize_object, parse_json_bytes
from validate_mechanism import ContractBundle, validate_instance


PUBLIC_RUN_EVENT_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:public-run-event:v2"
)
SURFACE_ROLES = {
    "AGENTS": {"UNKNOWN"},
    "CLAUDE": {"UNKNOWN"},
    "CODEX_AUTOMATION": {"AUTOMATION"},
    "CODEX_CLI": {"CLI"},
    "CODEX_DESKTOP": {"SUBAGENT", "USER"},
}


class PublicRunEventError(ValueError):
    """A public run event violates consumer-owned semantics."""


def _parse_utc(value: str) -> dt.datetime:
    try:
        return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=dt.timezone.utc
        )
    except ValueError as exc:
        raise PublicRunEventError("RUN_EVENT_UTC_TIMESTAMP_INVALID") from exc


def validate_public_run_event(
    bundle: ContractBundle,
    instance: Any,
    *,
    expected_bundle_digest: str,
) -> Mapping[str, Any]:
    """Validate one parsed event against schema, privacy, digest and semantics."""
    validate_instance(
        bundle,
        instance,
        PUBLIC_RUN_EVENT_SCHEMA_ID,
        expected_bundle_digest=expected_bundle_digest,
        public=True,
    )
    if not isinstance(instance, dict):  # enforced by schema; keeps typing honest.
        raise PublicRunEventError("RUN_EVENT_ROOT_NOT_OBJECT")

    surface = instance["surface_class"]
    role = instance["actor_role"]
    if role not in SURFACE_ROLES.get(surface, set()):
        raise PublicRunEventError(
            f"RUN_EVENT_SURFACE_ACTOR_ROLE_INVALID:{surface}:{role}"
        )

    if instance["binding_state"] == "BOUND":
        if surface not in {"CODEX_AUTOMATION", "CODEX_CLI"}:
            raise PublicRunEventError("RUN_EVENT_BOUND_SURFACE_INELIGIBLE")
        controlled = instance["controlled_invocation"]
        if controlled["surface_class"] != surface:
            raise PublicRunEventError("RUN_EVENT_CONTROLLED_SURFACE_MISMATCH")
        if _parse_utc(controlled["observed_at"]) > _parse_utc(
            instance["occurred_at"]
        ):
            raise PublicRunEventError(
                "RUN_EVENT_INVOCATION_EVIDENCE_AFTER_EVENT"
            )

    if (
        instance["event_type"] == "BINDING_CORRECTION"
        and instance["supersedes_event_uid"] == instance["event_uid"]
    ):
        raise PublicRunEventError("RUN_EVENT_CANNOT_SUPERSEDE_SELF")

    metrics = instance["metrics"]
    measured = metrics["token_usage_status"] == "MEASURED"
    token_values = (metrics["input_tokens"], metrics["output_tokens"])
    if measured != all(value is not None for value in token_values):
        raise PublicRunEventError(
            "RUN_EVENT_TOKEN_MEASUREMENT_STATE_MISMATCH"
        )
    if not measured and any(value is not None for value in token_values):
        raise PublicRunEventError("RUN_EVENT_UNMEASURED_TOKENS_MUST_BE_NULL")
    return instance


def parse_canonical_public_run_event(
    bundle: ContractBundle,
    raw_record: bytes,
    *,
    expected_bundle_digest: str,
) -> Mapping[str, Any]:
    """Parse exactly one unframed RFC 8785 record and validate it."""
    instance = parse_json_bytes(raw_record)
    if canonicalize_object(instance) != raw_record:
        raise PublicRunEventError("RUN_EVENT_RECORD_NOT_RFC8785_JCS")
    return validate_public_run_event(
        bundle,
        instance,
        expected_bundle_digest=expected_bundle_digest,
    )
