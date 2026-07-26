#!/usr/bin/env python3
"""Build/check non-active Mechanism M-066 capacity budget evidence."""

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

from CodexSkills.governance.performance.capacity_budgets import (  # noqa: E402
    BUDGET_SCHEMA_ID,
    BUDGET_SELF_POINTER,
    CACHE_KEY_FIELDS,
    CANDIDATE_BUNDLE_DIGEST,
    MAX_SHARD_BYTES,
    PROFILE_SCHEMA_ID,
    PROFILE_SELF_POINTER,
    PROTOCOL_REVISION,
    SCENARIOS,
    SOURCE_CLASSES,
    build_budget_contract,
    validate_budget_contract,
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
PERFORMANCE_DIR = GOVERNANCE_DIR / "performance"
SCHEMA_DIR = PERFORMANCE_DIR / "schemas"
COMPONENT_PATH = PERFORMANCE_DIR / "capacity_budgets.py"
BUDGET_PATH = PERFORMANCE_DIR / "performance-capacity-budget.json"
READINESS_PATH = PERFORMANCE_DIR / "performance-capacity-readiness.json"
PROFILE_SCHEMA_PATH = (
    SCHEMA_DIR / "performance-capacity-profile.schema.json"
)
BUDGET_SCHEMA_PATH = (
    SCHEMA_DIR / "performance-capacity-budget.schema.json"
)
READINESS_SCHEMA_PATH = (
    SCHEMA_DIR / "performance-capacity-readiness.schema.json"
)
VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

READINESS_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:performance-capacity-readiness:v1"
)
NEXT_PHASE = "MECHANISM_DASHBOARDS_ACTIONABLE_ALERTS"
CANDIDATE_GIT_OBJECT = (
    "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5"
)
CANDIDATE_MANIFEST_PATH = (
    "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
)
CANDIDATE_MANIFEST_RAW_SHA256 = (
    "66ad125629cab71739ff2bc266219f995f7a45998936ca720c6db678ee77e65a"
)

M065_GIT_OBJECT = (
    "sha1:f7195edd6fa992f8306491494e838fff34d425f1"
)
M065_READINESS_PATH = (
    "CodexSkills/governance/migration/"
    "read-only-migration-cutover-readiness.json"
)
M065_READINESS_RAW_SHA256 = (
    "839b363d904116d8657f78e10b53a1cd11c86f1d64f06064090e5a71b24ca02c"
)
M065_READINESS_SELF_DIGEST = (
    "049809b3292f5591fc63f899c2172e67da66bb0a152998e04a341bda401d1228"
)
M065_COMPONENT_PATH = (
    "CodexSkills/governance/migration/read_only_cutover.py"
)
M065_COMPONENT_RAW_SHA256 = (
    "0fccde44c02f8d4ad76ae2aca9e428a8a1c64855e0660027449035861911b9a1"
)
M065_SCHEMA_CONTRACTS = (
    (
        "CodexSkills/governance/migration/schemas/"
        "read-only-migration-observation.schema.json",
        "7507b62535395f52a8037ff5168c1b1e3019d04635b6a7015704c3b2bad8e304",
        "6d769bd378ee2526155fbfab29de89ec7754b41c026104a989a164a980505a97",
    ),
    (
        "CodexSkills/governance/migration/schemas/"
        "read-only-cutover-plan.schema.json",
        "bbdba195fd3f40c47d31694d239b65d282b51cb8604f511014bfbc8732e55792",
        "f800865090ce43f86ab78d69f306592a801f40faaad3bc2a167f20ecb3209d39",
    ),
    (
        "CodexSkills/governance/migration/schemas/"
        "read-only-migration-cutover-readiness.schema.json",
        "2ceaa60ec6e8ecc52d1ddb5d83e4ccc48fadcd5f0481f8286839262df7feb619",
        "d63de0996742f8943f905827b4eeb35ba0137b09b10acd3a84e45460ba717e9e",
    ),
)

M063_GIT_OBJECT = (
    "sha1:039f3844b36961f1d8432b9c0d86d6cda408f430"
)
M063_READINESS_PATH = (
    "CodexSkills/governance/retention/"
    "git-active-tree-365d-readiness.json"
)
M063_READINESS_RAW_SHA256 = (
    "91592f339854fb205993e96a67698d7b6ce8fc54afd3b226f3090dfd49ab86f2"
)
M063_READINESS_SELF_DIGEST = (
    "0bb6c1fb335115785495805ed001d6747a311dd1cbee335547beccaf8501df88"
)

M028_GLOBAL_INDEX_PATH = "CodexSkills/index.json"
M028_GLOBAL_INDEX_RAW_SHA256 = (
    "f3932c7297668415469064086f5f98830a75077a1b03ee96bb57952dfd1d09bd"
)

SCORECARD_SCHEMA_PATH = "CodexSkills/governance/schemas/scorecard.schema.json"
SCORECARD_SCHEMA_RAW_SHA256 = (
    "66716ff85edfce9ee0e608a8223bdf212ca74826eda82880e349c65de6c0b376"
)
SCORECARD_SCHEMA_SHA256 = (
    "6d47e264cf371b8cdf9e0679bc27c725b8fc37457b895c16a4eed639ac4f6f73"
)
DAILY_MANIFEST_SCHEMA_PATH = (
    "CodexSkills/registry/auto/schemas/public-v2/"
    "daily-run-shard-manifest.schema.json"
)
DAILY_MANIFEST_SCHEMA_RAW_SHA256 = (
    "5a38f1f4844b348f376a4c0633c16e7e4162df503c2403ac22e11a113bc1c820"
)
DAILY_MANIFEST_SCHEMA_SHA256 = (
    "e9214388da78376da47770934454d65a57659d1dde33fa0cb4e36b79e4665337"
)

REF = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:common-definitions:v1#/$defs/"
)


class PerformanceCapacityBuildError(ValueError):
    """M-066 evidence cannot be reproduced without weakening a gate."""


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
        raise PerformanceCapacityBuildError(code) from exc
    if not isinstance(value, dict):
        raise PerformanceCapacityBuildError(code)
    return value


def _git_blob(tagged_object: str, relative_path: str) -> bytes:
    if tagged_object.count(":") != 1:
        raise PerformanceCapacityBuildError("M066_GIT_OBJECT_INVALID")
    algorithm, object_id = tagged_object.split(":", 1)
    if algorithm != "sha1" or len(object_id) != 40:
        raise PerformanceCapacityBuildError("M066_GIT_OBJECT_INVALID")
    process = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", object_id + ":" + relative_path],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    if process.returncode != 0:
        raise PerformanceCapacityBuildError(
            "M066_GIT_BLOB_UNAVAILABLE:" + relative_path
        )
    return process.stdout


def _current(relative_path: str) -> bytes:
    path = REPO_ROOT.joinpath(*relative_path.split("/"))
    if not path.is_file() or path.is_symlink():
        raise PerformanceCapacityBuildError(
            "M066_CURRENT_FILE_INVALID:" + relative_path
        )
    return path.read_bytes()


def _pinned_json(
    tagged_object: str,
    relative_path: str,
    raw_digest: str,
    *,
    schema_digest: Optional[str] = None,
) -> Mapping[str, Any]:
    historical = _git_blob(tagged_object, relative_path)
    if _sha256(historical) != raw_digest:
        raise PerformanceCapacityBuildError(
            "M066_HISTORICAL_RAW_DRIFT:" + relative_path
        )
    if _current(relative_path) != historical:
        raise PerformanceCapacityBuildError(
            "M066_CURRENT_RAW_DRIFT:" + relative_path
        )
    value = _load(historical, "M066_JSON_INVALID:" + relative_path)
    if schema_digest is not None and canonical_digest(value) != schema_digest:
        raise PerformanceCapacityBuildError(
            "M066_SCHEMA_DIGEST_DRIFT:" + relative_path
        )
    return value


def _validate_dependencies() -> Mapping[str, Any]:
    m065 = _pinned_json(
        M065_GIT_OBJECT,
        M065_READINESS_PATH,
        M065_READINESS_RAW_SHA256,
    )
    if (
        m065.get("artifact_digest") != M065_READINESS_SELF_DIGEST
        or m065.get("artifact_digest")
        != canonical_digest(m065, "/artifact_digest")
        or m065.get("next_phase")
        != "MECHANISM_PERFORMANCE_CAPACITY_BUDGETS"
        or m065.get("task_contract", {}).get("implemented_task_ids")
        != ["M-065"]
    ):
        raise PerformanceCapacityBuildError("M066_M065_CONTRACT_INVALID")
    component = _git_blob(M065_GIT_OBJECT, M065_COMPONENT_PATH)
    if (
        _sha256(component) != M065_COMPONENT_RAW_SHA256
        or _current(M065_COMPONENT_PATH) != component
    ):
        raise PerformanceCapacityBuildError("M066_M065_COMPONENT_DRIFT")
    for path, raw_digest, schema_digest in M065_SCHEMA_CONTRACTS:
        _pinned_json(
            M065_GIT_OBJECT,
            path,
            raw_digest,
            schema_digest=schema_digest,
        )
    m063 = _pinned_json(
        M063_GIT_OBJECT,
        M063_READINESS_PATH,
        M063_READINESS_RAW_SHA256,
    )
    if (
        m063.get("artifact_digest") != M063_READINESS_SELF_DIGEST
        or m063.get("artifact_digest")
        != canonical_digest(m063, "/artifact_digest")
        or m063.get("task_contract", {}).get("completed_task_ids")
        != ["M-063"]
    ):
        raise PerformanceCapacityBuildError("M066_M063_CONTRACT_INVALID")
    m028_index = _pinned_json(
        M065_GIT_OBJECT,
        M028_GLOBAL_INDEX_PATH,
        M028_GLOBAL_INDEX_RAW_SHA256,
    )
    if (
        m028_index.get("schema") != "codex_skills_index.v2"
        or m028_index.get("skill_instance_count") != 90
        or not isinstance(m028_index.get("skills"), list)
        or len(m028_index["skills"]) != 90
    ):
        raise PerformanceCapacityBuildError("M066_M028_INDEX_INVALID")
    scorecard = _load(
        _git_blob(CANDIDATE_GIT_OBJECT, SCORECARD_SCHEMA_PATH),
        "M066_SCORECARD_SCHEMA_INVALID",
    )
    if (
        _sha256(_git_blob(CANDIDATE_GIT_OBJECT, SCORECARD_SCHEMA_PATH))
        != SCORECARD_SCHEMA_RAW_SHA256
        or canonical_digest(scorecard) != SCORECARD_SCHEMA_SHA256
        or _current(SCORECARD_SCHEMA_PATH)
        != _git_blob(CANDIDATE_GIT_OBJECT, SCORECARD_SCHEMA_PATH)
    ):
        raise PerformanceCapacityBuildError("M066_SCORECARD_SCHEMA_DRIFT")
    daily = _load(
        _git_blob(CANDIDATE_GIT_OBJECT, DAILY_MANIFEST_SCHEMA_PATH),
        "M066_DAILY_MANIFEST_SCHEMA_INVALID",
    )
    if (
        _sha256(_git_blob(CANDIDATE_GIT_OBJECT, DAILY_MANIFEST_SCHEMA_PATH))
        != DAILY_MANIFEST_SCHEMA_RAW_SHA256
        or canonical_digest(daily) != DAILY_MANIFEST_SCHEMA_SHA256
        or daily.get("properties", {}).get("max_part_bytes", {}).get("const")
        != MAX_SHARD_BYTES
        or _current(DAILY_MANIFEST_SCHEMA_PATH)
        != _git_blob(CANDIDATE_GIT_OBJECT, DAILY_MANIFEST_SCHEMA_PATH)
    ):
        raise PerformanceCapacityBuildError(
            "M066_DAILY_MANIFEST_SCHEMA_DRIFT"
        )
    return {"m028_index": m028_index, "m063": m063, "m065": m065}


def _ref(name: str) -> Mapping[str, str]:
    return {"$ref": REF + name}


def _closed(
    properties: Mapping[str, Any],
    required: Optional[Sequence[str]] = None,
) -> Mapping[str, Any]:
    return {
        "additionalProperties": False,
        "properties": dict(properties),
        "required": list(properties if required is None else required),
        "type": "object",
    }


def build_profile_schema() -> Mapping[str, Any]:
    cache_properties = {field: _ref("sha256") for field in CACHE_KEY_FIELDS}
    return {
        "$id": PROFILE_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"const": PROFILE_SCHEMA_ID},
            "protocol_revision": {"const": PROTOCOL_REVISION},
            "bundle_digest": {"const": CANDIDATE_BUNDLE_DIGEST},
            "profile_uid": _ref("typed_uid"),
            "owner_plane": {"const": "MECHANISM"},
            "status": {"const": "DRAFT_NON_ACTIVE"},
            "scenario": {"enum": list(SCENARIOS)},
            "cache_state": {"enum": ["COLD", "WARM"]},
            "environment_fingerprint_digest": _ref("sha256"),
            "input_contract_digest": _ref("sha256"),
            "input_count": _ref("nonnegative_count"),
            "processed_count": _ref("nonnegative_count"),
            "skipped_count": _ref("nonnegative_count"),
            "sampled_count": _ref("nonnegative_count"),
            "duration_ms": _ref("nonnegative_count"),
            "peak_memory_bytes": _ref("nonnegative_count"),
            "output_artifact_bytes": _ref("nonnegative_count"),
            "commit_count": _ref("nonnegative_count"),
            "source_classes": {
                "items": {"enum": list(SOURCE_CLASSES)},
                "maxItems": 4,
                "type": "array",
                "uniqueItems": True,
            },
            "truncated": {"type": "boolean"},
            "watermark_advanced": {"type": "boolean"},
            "cache_key_digests": _closed(cache_properties, ()),
            "graph_pairing_mode": {
                "enum": [
                    "FILTERED_CANDIDATE_SET",
                    "NOT_APPLICABLE",
                    "UNCONDITIONAL_ALL_PAIRS",
                ]
            },
            "growth_warning_horizon_days": _ref("nonnegative_count"),
            "evidence_bundle_digest": _ref("sha256"),
        },
        "required": [
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
        ],
        "title": "Mechanism M-066 performance/capacity profile",
        "type": "object",
    }


def build_budget_schema(
    budget: Mapping[str, Any],
) -> Mapping[str, Any]:
    properties = {
        key: {"const": value}
        for key, value in budget.items()
        if key != "artifact_digest"
    }
    properties["artifact_digest"] = _ref("sha256")
    return {
        "$id": BUDGET_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(budget),
        "title": "Mechanism M-066 provisional capacity budget",
        "type": "object",
    }


def _extend_bundle(
    base: ContractBundle,
    additions: Mapping[str, Mapping[str, Any]],
    pointers: Mapping[str, str],
) -> ContractBundle:
    schemas = dict(base.schemas)
    self_pointers = dict(base.self_digest_pointers)
    for schema_id, schema in additions.items():
        if schema_id in schemas:
            raise PerformanceCapacityBuildError(
                "M066_SCHEMA_REBIND_FORBIDDEN:" + schema_id
            )
        schemas[schema_id] = schema
        self_pointers[schema_id] = pointers[schema_id]
    try:
        registry, checker = build_registry(schemas)
    except ContractError as exc:
        raise PerformanceCapacityBuildError(
            "M066_SCHEMA_CLOSURE_INVALID:" + str(exc)
        ) from exc
    return ContractBundle(
        schemas=schemas,
        registry=registry,
        format_checker=checker,
        self_digest_pointers=self_pointers,
        policies=base.policies,
        protocol_revision=base.protocol_revision,
    )


def _descriptor(
    schema_id: str,
    path: str,
    raw: bytes,
    schema_digest: str,
    self_pointer: str,
) -> Mapping[str, Any]:
    return {
        "schema_version": schema_id,
        "canonical_path": path,
        "content_digest": _sha256(raw),
        "schema_sha256": schema_digest,
        "self_digest_pointer": self_pointer,
    }


def _build_readiness(
    budget: Mapping[str, Any],
    budget_schema: Mapping[str, Any],
    profile_schema: Mapping[str, Any],
    dependencies: Mapping[str, Any],
) -> Mapping[str, Any]:
    budget_raw = _render(budget)
    budget_schema_raw = _render(budget_schema)
    profile_schema_raw = _render(profile_schema)
    value: Dict[str, Any] = {
        "schema_version": READINESS_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "status": (
            "DRAFT_NON_ACTIVE_PERFORMANCE_CAPACITY_BUDGETS_"
            "IMPLEMENTED_UNCALIBRATED"
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
            "m065_predecessor": {
                "verified_git_object_id": M065_GIT_OBJECT,
                "canonical_path": M065_READINESS_PATH,
                "content_digest": M065_READINESS_RAW_SHA256,
                "artifact_digest": M065_READINESS_SELF_DIGEST,
                "status": dependencies["m065"]["status"],
            },
            "m063_retention_dependency": {
                "verified_git_object_id": M063_GIT_OBJECT,
                "canonical_path": M063_READINESS_PATH,
                "content_digest": M063_READINESS_RAW_SHA256,
                "artifact_digest": M063_READINESS_SELF_DIGEST,
                "status": dependencies["m063"]["status"],
            },
            "m028_global_index_dependency": {
                "verified_git_object_id": M065_GIT_OBJECT,
                "canonical_path": M028_GLOBAL_INDEX_PATH,
                "content_digest": M028_GLOBAL_INDEX_RAW_SHA256,
                "schema": dependencies["m028_index"]["schema"],
                "skill_instance_count": dependencies["m028_index"][
                    "skill_instance_count"
                ],
                "byte_equivalent_rebuild_replayed": False,
                "current_source_freshness_verified": False,
            },
            "m043_scorecard_schema": {
                "verified_git_object_id": CANDIDATE_GIT_OBJECT,
                "canonical_path": SCORECARD_SCHEMA_PATH,
                "content_digest": SCORECARD_SCHEMA_RAW_SHA256,
                "schema_sha256": SCORECARD_SCHEMA_SHA256,
            },
            "daily_manifest_schema": {
                "verified_git_object_id": CANDIDATE_GIT_OBJECT,
                "canonical_path": DAILY_MANIFEST_SCHEMA_PATH,
                "content_digest": DAILY_MANIFEST_SCHEMA_RAW_SHA256,
                "schema_sha256": DAILY_MANIFEST_SCHEMA_SHA256,
                "max_shard_bytes": MAX_SHARD_BYTES,
            },
            "repository_self_report_is_not_trust_root": True,
        },
        "implementation_contract": {
            "component_path": (
                "CodexSkills/governance/performance/capacity_budgets.py"
            ),
            "content_digest": _sha256(COMPONENT_PATH.read_bytes()),
            "capability_mode": "PURE_IMMUTABLE_OBJECTS_ONLY",
            "budget": {
                **_descriptor(
                    BUDGET_SCHEMA_ID,
                    (
                        "CodexSkills/governance/performance/schemas/"
                        "performance-capacity-budget.schema.json"
                    ),
                    budget_schema_raw,
                    canonical_digest(budget_schema),
                    BUDGET_SELF_POINTER,
                ),
                "instance": {
                    "canonical_path": (
                        "CodexSkills/governance/performance/"
                        "performance-capacity-budget.json"
                    ),
                    "content_digest": _sha256(budget_raw),
                    "artifact_digest": budget["artifact_digest"],
                },
            },
            "profile_schema": _descriptor(
                PROFILE_SCHEMA_ID,
                (
                    "CodexSkills/governance/performance/schemas/"
                    "performance-capacity-profile.schema.json"
                ),
                profile_schema_raw,
                canonical_digest(profile_schema),
                PROFILE_SELF_POINTER,
            ),
            "silent_sampling_permitted": False,
            "source_skip_permitted": False,
            "event_drop_permitted": False,
            "truncation_permitted": False,
            "failure_watermark_advance_permitted": False,
            "real_profiler_capability_present": False,
            "filesystem_capability_present": False,
            "cache_mutation_capability_present": False,
            "state_capability_present": False,
            "publisher_capability_present": False,
        },
        "calibration_state": {
            "state": "UNCALIBRATED",
            "real_profile_count": 0,
            "hardware_baseline_verified": False,
            "cold_cache_baseline_verified": False,
            "warm_cache_baseline_verified": False,
            "ten_thousand_event_baseline_verified": False,
            "production_sla_proven": False,
            "provisional_budgets_enforced_as_integrity_guards": True,
        },
        "dependency_evidence": {
            "m028_status": (
                "GENERATED_INDEX_BYTES_PINNED_REBUILD_GATE_NOT_REPLAYED"
            ),
            "m043_status": "SCORECARD_SCHEMA_VERIFIED",
            "m063_status": "GIT_ACTIVE_TREE_POLICY_VERIFIED",
            "runtime_capacity_readiness": "BLOCKED_UNCALIBRATED",
        },
        "nonmutation": {
            "auto_plane_unchanged": True,
            "openai_database_unchanged": True,
            "candidate_bundle_unchanged": True,
            "real_profile_executed": False,
            "cache_write_permitted": False,
            "shard_write_permitted": False,
            "state_write_permitted": False,
            "watermark_advance_permitted": False,
            "canonical_publication_permitted": False,
            "activation_forbidden": True,
            "version_file_created": False,
        },
        "task_contract": {
            "dependency_task_ids": ["M-028", "M-043", "M-063"],
            "implemented_task_ids": ["M-066"],
            "runtime_calibration_status": "BLOCKED_UNCALIBRATED",
            "pending_task_ids": ["M-067"],
            "required_output_code": (
                "PROFILING_SHARD_CACHE_GROWTH_BUDGETS"
            ),
            "done_gate": "NO_SILENT_SAMPLING_OR_SKIPPED_SOURCE",
        },
        "schema_closure_count": 34,
        "policy_count": 5,
        "real_execution_permitted": False,
        "next_phase": NEXT_PHASE,
        "self_digest_pointer": "/artifact_digest",
        "task_pack_revision": "v0.0.0.2",
        "artifact_digest": "0" * 64,
    }
    value["artifact_digest"] = canonical_digest(value, "/artifact_digest")
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
        "additionalProperties": False,
        "properties": properties,
        "required": list(readiness),
        "title": "Mechanism M-066 performance/capacity readiness",
        "type": "object",
    }


def _documents() -> Mapping[Path, bytes]:
    dependencies = _validate_dependencies()
    acceptance = load_au040_acceptance()
    if (
        len(acceptance.bundle.schemas) != 31
        or len(acceptance.bundle.policies) != 5
        or acceptance.bundle.protocol_revision != PROTOCOL_REVISION
    ):
        raise PerformanceCapacityBuildError("M066_CANDIDATE_INVALID")
    budget = build_budget_contract()
    validate_budget_contract(budget)
    profile_schema = build_profile_schema()
    budget_schema = build_budget_schema(budget)
    contract = _extend_bundle(
        acceptance.bundle,
        {
            PROFILE_SCHEMA_ID: profile_schema,
            BUDGET_SCHEMA_ID: budget_schema,
        },
        {
            PROFILE_SCHEMA_ID: PROFILE_SELF_POINTER,
            BUDGET_SCHEMA_ID: BUDGET_SELF_POINTER,
        },
    )
    try:
        validate_instance(
            contract,
            budget,
            BUDGET_SCHEMA_ID,
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            verify_digest=True,
            public=True,
        )
        scan_public_value(budget, contract.policies)
    except ContractError as exc:
        raise PerformanceCapacityBuildError(
            "M066_BUDGET_INVALID:" + str(exc)
        ) from exc
    readiness = _build_readiness(
        budget,
        budget_schema,
        profile_schema,
        dependencies,
    )
    readiness_schema = build_readiness_schema(readiness)
    final_contract = _extend_bundle(
        contract,
        {READINESS_SCHEMA_ID: readiness_schema},
        {READINESS_SCHEMA_ID: "/artifact_digest"},
    )
    if len(final_contract.schemas) != 34:
        raise PerformanceCapacityBuildError("M066_SCHEMA_CLOSURE_INVALID")
    try:
        validate_instance(
            final_contract,
            readiness,
            READINESS_SCHEMA_ID,
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            verify_digest=True,
            public=True,
        )
        scan_public_value(readiness, final_contract.policies)
    except ContractError as exc:
        raise PerformanceCapacityBuildError(
            "M066_READINESS_INVALID:" + str(exc)
        ) from exc
    return {
        BUDGET_PATH: _render(budget),
        READINESS_PATH: _render(readiness),
        PROFILE_SCHEMA_PATH: _render(profile_schema),
        BUDGET_SCHEMA_PATH: _render(budget_schema),
        READINESS_SCHEMA_PATH: _render(readiness_schema),
    }


def _write() -> None:
    documents = _documents()
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    for path, raw in documents.items():
        path.write_bytes(raw)


def _check() -> None:
    for path, expected in _documents().items():
        if not path.is_file() or path.is_symlink():
            raise PerformanceCapacityBuildError(
                "M066_ARTIFACT_FILE_INVALID:" + str(path.relative_to(REPO_ROOT))
            )
        if path.read_bytes() != expected:
            raise PerformanceCapacityBuildError(
                "M066_ARTIFACT_NOT_BYTE_EQUIVALENT:"
                + str(path.relative_to(REPO_ROOT))
            )
    if VERSION_PATH.exists():
        raise PerformanceCapacityBuildError("M066_ACTIVE_VERSION_FORBIDDEN")


def _main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        _write()
    else:
        _check()
    print(
        "PERFORMANCE_CAPACITY_BUDGETS_OK "
        "implementation=true calibration=UNCALIBRATED "
        "sampling=false source_skip=false production_sla=false"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except (ContractError, PerformanceCapacityBuildError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
