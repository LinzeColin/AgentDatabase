"""Pure M-066 performance and capacity budget contract.

The guard treats Task Pack budgets as provisional thresholds that require a
real hardware/workload/cold-warm baseline before production calibration.  It
never trades completeness for speed: sampling, skipping, truncation, missing
sources, incomplete processing, or watermark advancement on failure all fail
closed.

The module accepts immutable objects only and has no clock, profiler,
filesystem, Git, cache, state, watermark, shard-writer, publisher, or network
capability.
"""

from __future__ import annotations

import copy
import re
from typing import Any, Dict, Mapping, Optional, Sequence

from CodexSkills.governance.tools.canonical_json import canonical_digest


SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
PROTOCOL_REVISION = (
    "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
)
PROFILE_SCHEMA_ID = SCHEMA_PREFIX + "performance-capacity-profile:v1"
BUDGET_SCHEMA_ID = SCHEMA_PREFIX + "performance-capacity-budget:v1"
PROFILE_SELF_POINTER = "/evidence_bundle_digest"
BUDGET_SELF_POINTER = "/artifact_digest"
CANDIDATE_BUNDLE_DIGEST = (
    "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
)

SOURCE_CLASSES = ("AGENTS", "CLAUDE", "CODEX", "CODEX_SYSTEM")
SCENARIOS = (
    "CAPABILITY_GRAPH_PAIRING",
    "CANONICAL_TRANSACTION",
    "EVALUATION_CACHE",
    "FOUR_SOURCE_FULL_INVENTORY",
    "PUBLIC_EVENTS_10000",
    "REGISTRY_FAST_PATH",
    "REPOSITORY_GROWTH_FORECAST",
    "SINGLE_GIT_SHARD",
)
CACHE_STATES = ("COLD", "WARM")
OUTCOMES = (
    "BLOCKED_INCOMPLETE",
    "OVER_BUDGET_FAIL_CLOSED",
    "WITHIN_PROVISIONAL_BUDGET",
)
REMEDIATIONS = {
    "CAPABILITY_GRAPH_PAIRING": "FILTER_CANDIDATES_BEFORE_PAIR_ANALYSIS",
    "CANONICAL_TRANSACTION": "ABORT_TRANSACTION_NO_WATERMARK_ADVANCE",
    "EVALUATION_CACHE": "RECOMPUTE_WITH_COMPLETE_DIGEST_KEY",
    "FOUR_SOURCE_FULL_INVENTORY": "DIAGNOSE_PER_SOURCE_NO_SKIP",
    "PUBLIC_EVENTS_10000": "BACKPRESSURE_AND_ROTATE_NO_EVENT_DROP",
    "REGISTRY_FAST_PATH": "PROFILE_AND_RUN_COMPLETE_PATH",
    "REPOSITORY_GROWTH_FORECAST": "OWNER_MAJOR_ARCHITECTURE_PROPOSAL",
    "SINGLE_GIT_SHARD": "ROTATE_NEW_SHARD_NO_TRUNCATION",
}

REGISTRY_FAST_PATH_MAX_MS = 60_000
FULL_INVENTORY_MAX_MS = 300_000
PUBLIC_EVENTS_BATCH_COUNT = 10_000
PUBLIC_EVENTS_MAX_MS = 600_000
PUBLIC_EVENTS_MAX_PEAK_BYTES = 512 * 1024 * 1024
MAX_SHARD_BYTES = 20 * 1024 * 1024
MAX_TRANSACTION_COMMITS = 1
GROWTH_WARNING_MIN_DAYS = 90

PROFILE_FIELDS = (
    "schema_version",
    "protocol_revision",
    "bundle_digest",
    "profile_uid",
    "owner_plane",
    "status",
    "scenario",
    "cache_state",
    "environment_fingerprint_digest",
    "input_contract_digest",
    "input_count",
    "processed_count",
    "skipped_count",
    "sampled_count",
    "duration_ms",
    "peak_memory_bytes",
    "output_artifact_bytes",
    "commit_count",
    "source_classes",
    "truncated",
    "watermark_advanced",
    "cache_key_digests",
    "graph_pairing_mode",
    "growth_warning_horizon_days",
    "evidence_bundle_digest",
)
CACHE_KEY_FIELDS = (
    "dataset_manifest_digests",
    "environment_fingerprint_digest",
    "evaluator_manifest_digests",
    "model_snapshot_digest",
    "skill_version_record_digest",
    "tool_manifest_digest",
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UID_RE = re.compile(r"^[a-z][a-z0-9]{1,11}_[0-7][0-9A-HJKMNP-TV-Z]{25}$")


class CapacityBudgetError(ValueError):
    """One M-066 completeness or budget invariant failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> None:
    raise CapacityBudgetError(code)


def _nonnegative(value: Any, code: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        or value > 9007199254740991
    ):
        _fail(code)
    return value


def _digest(value: Any, code: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        _fail(code)
    return value


def build_budget_contract() -> Mapping[str, Any]:
    """Return the fixed provisional M-066 budget and integrity contract."""

    value: Dict[str, Any] = {
        "schema_version": BUDGET_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "artifact_uid": "pcb_01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "owner_plane": "MECHANISM",
        "status": "DRAFT_NON_ACTIVE_UNCALIBRATED",
        "calibration": {
            "state": "UNCALIBRATED",
            "provisional_budget_is_production_sla": False,
            "real_hardware_profile_required": True,
            "real_workload_manifest_required": True,
            "cold_and_warm_profiles_required": True,
            "calibration_change_requires_evidence": True,
        },
        "budgets": [
            {
                "scenario": "REGISTRY_FAST_PATH",
                "threshold": {
                    "duration_ms_max": REGISTRY_FAST_PATH_MAX_MS,
                    "full_source_coverage_required": True,
                },
                "remediation": REMEDIATIONS["REGISTRY_FAST_PATH"],
            },
            {
                "scenario": "FOUR_SOURCE_FULL_INVENTORY",
                "threshold": {
                    "duration_ms_max": FULL_INVENTORY_MAX_MS,
                    "required_source_classes": list(SOURCE_CLASSES),
                },
                "remediation": REMEDIATIONS[
                    "FOUR_SOURCE_FULL_INVENTORY"
                ],
            },
            {
                "scenario": "PUBLIC_EVENTS_10000",
                "threshold": {
                    "input_count": PUBLIC_EVENTS_BATCH_COUNT,
                    "duration_ms_max": PUBLIC_EVENTS_MAX_MS,
                    "peak_memory_bytes_max": (
                        PUBLIC_EVENTS_MAX_PEAK_BYTES
                    ),
                },
                "remediation": REMEDIATIONS["PUBLIC_EVENTS_10000"],
            },
            {
                "scenario": "SINGLE_GIT_SHARD",
                "threshold": {
                    "artifact_bytes_max": MAX_SHARD_BYTES,
                    "rotation_required_above_limit": True,
                },
                "remediation": REMEDIATIONS["SINGLE_GIT_SHARD"],
            },
            {
                "scenario": "CANONICAL_TRANSACTION",
                "threshold": {
                    "commit_count_max": MAX_TRANSACTION_COMMITS,
                    "watermark_requires_remote_readback": True,
                },
                "remediation": REMEDIATIONS[
                    "CANONICAL_TRANSACTION"
                ],
            },
            {
                "scenario": "REPOSITORY_GROWTH_FORECAST",
                "threshold": {
                    "warning_horizon_days_min": (
                        GROWTH_WARNING_MIN_DAYS
                    ),
                    "silent_sampling_permitted": False,
                },
                "remediation": REMEDIATIONS[
                    "REPOSITORY_GROWTH_FORECAST"
                ],
            },
            {
                "scenario": "CAPABILITY_GRAPH_PAIRING",
                "threshold": {
                    "pairing_mode": "FILTERED_CANDIDATE_SET",
                    "unconditional_all_pairs_permitted": False,
                },
                "remediation": REMEDIATIONS[
                    "CAPABILITY_GRAPH_PAIRING"
                ],
            },
            {
                "scenario": "EVALUATION_CACHE",
                "threshold": {
                    "required_cache_key_fields": list(CACHE_KEY_FIELDS),
                    "partial_cache_key_permitted": False,
                },
                "remediation": REMEDIATIONS["EVALUATION_CACHE"],
            },
        ],
        "completeness_invariants": {
            "input_count_must_equal_processed_count": True,
            "skipped_count": 0,
            "sampled_count": 0,
            "truncation_permitted": False,
            "source_skip_permitted": False,
            "event_drop_permitted": False,
            "silent_sampling_permitted": False,
            "watermark_advance_on_failure_permitted": False,
        },
        "artifact_contract": {
            "content_addressed": True,
            "deduplication_required": True,
            "oversize_behavior": "FAIL_CLOSED_OR_ROTATE_WITHOUT_TRUNCATION",
        },
        "artifact_digest": "0" * 64,
    }
    value["artifact_digest"] = canonical_digest(
        value,
        BUDGET_SELF_POINTER,
    )
    return value


def validate_budget_contract(value: Mapping[str, Any]) -> None:
    """Reject weakened or self-consistent budget-contract drift."""

    expected = build_budget_contract()
    if value != expected:
        _fail("CAPACITY_BUDGET_CONTRACT_DRIFT")
    if value["artifact_digest"] != canonical_digest(
        value,
        BUDGET_SELF_POINTER,
    ):
        _fail("CAPACITY_BUDGET_DIGEST_MISMATCH")


def build_profile(
    *,
    profile_uid: str,
    scenario: str,
    cache_state: str,
    environment_fingerprint_digest: str,
    input_contract_digest: str,
    input_count: int,
    processed_count: int,
    skipped_count: int = 0,
    sampled_count: int = 0,
    duration_ms: int = 0,
    peak_memory_bytes: int = 0,
    output_artifact_bytes: int = 0,
    commit_count: int = 0,
    source_classes: Sequence[str] = (),
    truncated: bool = False,
    watermark_advanced: bool = False,
    cache_key_digests: Optional[Mapping[str, str]] = None,
    graph_pairing_mode: str = "NOT_APPLICABLE",
    growth_warning_horizon_days: int = 0,
) -> Mapping[str, Any]:
    """Normalize and self-digest one immutable performance profile."""

    value: Dict[str, Any] = {
        "schema_version": PROFILE_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        "profile_uid": profile_uid,
        "owner_plane": "MECHANISM",
        "status": "DRAFT_NON_ACTIVE",
        "scenario": scenario,
        "cache_state": cache_state,
        "environment_fingerprint_digest": environment_fingerprint_digest,
        "input_contract_digest": input_contract_digest,
        "input_count": input_count,
        "processed_count": processed_count,
        "skipped_count": skipped_count,
        "sampled_count": sampled_count,
        "duration_ms": duration_ms,
        "peak_memory_bytes": peak_memory_bytes,
        "output_artifact_bytes": output_artifact_bytes,
        "commit_count": commit_count,
        "source_classes": list(source_classes),
        "truncated": truncated,
        "watermark_advanced": watermark_advanced,
        "cache_key_digests": dict(cache_key_digests or {}),
        "graph_pairing_mode": graph_pairing_mode,
        "growth_warning_horizon_days": growth_warning_horizon_days,
        "evidence_bundle_digest": "0" * 64,
    }
    value["evidence_bundle_digest"] = canonical_digest(
        value,
        PROFILE_SELF_POINTER,
    )
    validate_profile(value)
    return value


def validate_profile(value: Mapping[str, Any]) -> None:
    """Validate profile framing and recompute its self digest."""

    if not isinstance(value, dict) or set(value) != set(PROFILE_FIELDS):
        _fail("CAPACITY_PROFILE_FIELDS_INVALID")
    if (
        value["schema_version"] != PROFILE_SCHEMA_ID
        or value["protocol_revision"] != PROTOCOL_REVISION
        or value["bundle_digest"] != CANDIDATE_BUNDLE_DIGEST
        or value["owner_plane"] != "MECHANISM"
        or value["status"] != "DRAFT_NON_ACTIVE"
    ):
        _fail("CAPACITY_PROFILE_CONTEXT_INVALID")
    if (
        not isinstance(value["profile_uid"], str)
        or UID_RE.fullmatch(value["profile_uid"]) is None
    ):
        _fail("CAPACITY_PROFILE_UID_INVALID")
    if value["scenario"] not in SCENARIOS:
        _fail("CAPACITY_PROFILE_SCENARIO_INVALID")
    if value["cache_state"] not in CACHE_STATES:
        _fail("CAPACITY_PROFILE_CACHE_STATE_INVALID")
    _digest(
        value["environment_fingerprint_digest"],
        "CAPACITY_HARDWARE_DIGEST_INVALID",
    )
    _digest(
        value["input_contract_digest"],
        "CAPACITY_WORKLOAD_DIGEST_INVALID",
    )
    for field in (
        "input_count",
        "processed_count",
        "skipped_count",
        "sampled_count",
        "duration_ms",
        "peak_memory_bytes",
        "output_artifact_bytes",
        "commit_count",
        "growth_warning_horizon_days",
    ):
        _nonnegative(value[field], "CAPACITY_PROFILE_COUNT_INVALID:" + field)
    sources = value["source_classes"]
    if (
        not isinstance(sources, list)
        or sources != sorted(set(sources))
        or any(source not in SOURCE_CLASSES for source in sources)
    ):
        _fail("CAPACITY_PROFILE_SOURCE_SET_INVALID")
    for field in ("truncated", "watermark_advanced"):
        if not isinstance(value[field], bool):
            _fail("CAPACITY_PROFILE_BOOL_INVALID:" + field)
    cache_keys = value["cache_key_digests"]
    if not isinstance(cache_keys, dict):
        _fail("CAPACITY_CACHE_KEY_INVALID")
    for key, digest in cache_keys.items():
        if key not in CACHE_KEY_FIELDS:
            _fail("CAPACITY_CACHE_KEY_FIELD_INVALID")
        _digest(digest, "CAPACITY_CACHE_KEY_DIGEST_INVALID")
    if value["graph_pairing_mode"] not in {
        "FILTERED_CANDIDATE_SET",
        "NOT_APPLICABLE",
        "UNCONDITIONAL_ALL_PAIRS",
    }:
        _fail("CAPACITY_GRAPH_PAIRING_MODE_INVALID")
    if value["evidence_bundle_digest"] != canonical_digest(
        value,
        PROFILE_SELF_POINTER,
    ):
        _fail("CAPACITY_PROFILE_DIGEST_MISMATCH")


def evaluate_profile(
    profile: Mapping[str, Any],
    budget: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Recompute completeness and budget outcome without caller booleans."""

    validate_profile(profile)
    validate_budget_contract(budget)
    blockers = []
    if profile["processed_count"] != profile["input_count"]:
        blockers.append("INPUT_PROCESSED_COUNT_MISMATCH")
    if profile["skipped_count"] != 0:
        blockers.append("SKIPPED_INPUT_NONZERO")
    if profile["sampled_count"] != 0:
        blockers.append("SAMPLED_INPUT_NONZERO")
    if profile["truncated"]:
        blockers.append("TRUNCATION_FORBIDDEN")
    scenario = profile["scenario"]
    if scenario in {
        "REGISTRY_FAST_PATH",
        "FOUR_SOURCE_FULL_INVENTORY",
    } and tuple(profile["source_classes"]) != SOURCE_CLASSES:
        blockers.append("FOUR_SOURCE_COVERAGE_INCOMPLETE")
    if scenario == "PUBLIC_EVENTS_10000" and profile["input_count"] != (
        PUBLIC_EVENTS_BATCH_COUNT
    ):
        blockers.append("PUBLIC_EVENT_BATCH_COUNT_INVALID")
    if scenario == "EVALUATION_CACHE" and set(
        profile["cache_key_digests"]
    ) != set(CACHE_KEY_FIELDS):
        blockers.append("EVALUATION_CACHE_KEY_INCOMPLETE")
    if (
        scenario == "CAPABILITY_GRAPH_PAIRING"
        and profile["graph_pairing_mode"] != "FILTERED_CANDIDATE_SET"
    ):
        blockers.append("UNFILTERED_ALL_PAIR_ANALYSIS_FORBIDDEN")

    over_budget = []
    if (
        scenario == "REGISTRY_FAST_PATH"
        and profile["duration_ms"] > REGISTRY_FAST_PATH_MAX_MS
    ):
        over_budget.append("REGISTRY_FAST_PATH_DURATION_EXCEEDED")
    if (
        scenario == "FOUR_SOURCE_FULL_INVENTORY"
        and profile["duration_ms"] > FULL_INVENTORY_MAX_MS
    ):
        over_budget.append("FULL_INVENTORY_DURATION_EXCEEDED")
    if scenario == "PUBLIC_EVENTS_10000":
        if profile["duration_ms"] > PUBLIC_EVENTS_MAX_MS:
            over_budget.append("PUBLIC_EVENT_DURATION_EXCEEDED")
        if profile["peak_memory_bytes"] > PUBLIC_EVENTS_MAX_PEAK_BYTES:
            over_budget.append("PUBLIC_EVENT_MEMORY_EXCEEDED")
    if (
        scenario == "SINGLE_GIT_SHARD"
        and profile["output_artifact_bytes"] > MAX_SHARD_BYTES
    ):
        over_budget.append("SHARD_SIZE_EXCEEDED")
    if (
        scenario == "CANONICAL_TRANSACTION"
        and profile["commit_count"] > MAX_TRANSACTION_COMMITS
    ):
        over_budget.append("TRANSACTION_COMMIT_COUNT_EXCEEDED")
    if (
        scenario == "REPOSITORY_GROWTH_FORECAST"
        and profile["growth_warning_horizon_days"]
        < GROWTH_WARNING_MIN_DAYS
    ):
        over_budget.append("GROWTH_WARNING_HORIZON_INSUFFICIENT")

    if blockers:
        outcome = "BLOCKED_INCOMPLETE"
    elif over_budget:
        outcome = "OVER_BUDGET_FAIL_CLOSED"
    else:
        outcome = "WITHIN_PROVISIONAL_BUDGET"
    if outcome != "WITHIN_PROVISIONAL_BUDGET" and profile[
        "watermark_advanced"
    ]:
        blockers.append("WATERMARK_ADVANCED_ON_FAILURE")
        outcome = "BLOCKED_INCOMPLETE"
    return {
        "profile_uid": profile["profile_uid"],
        "evidence_digest": profile["evidence_bundle_digest"],
        "scenario": scenario,
        "outcome": outcome,
        "completeness_blocker_codes": sorted(set(blockers)),
        "budget_exceedance_codes": sorted(set(over_budget)),
        "remediation": REMEDIATIONS[scenario],
        "watermark_advance_permitted": (
            outcome == "WITHIN_PROVISIONAL_BUDGET"
        ),
        "production_sla_proven": False,
    }


__all__ = [
    "BUDGET_SCHEMA_ID",
    "BUDGET_SELF_POINTER",
    "CACHE_KEY_FIELDS",
    "CANDIDATE_BUNDLE_DIGEST",
    "CapacityBudgetError",
    "MAX_SHARD_BYTES",
    "PROFILE_SCHEMA_ID",
    "PROFILE_SELF_POINTER",
    "PROTOCOL_REVISION",
    "SCENARIOS",
    "SOURCE_CLASSES",
    "build_budget_contract",
    "build_profile",
    "evaluate_profile",
    "validate_budget_contract",
    "validate_profile",
]
