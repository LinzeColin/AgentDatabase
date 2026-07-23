#!/usr/bin/env python3
"""Offline semantic validator for the non-active AU-040 transport draft."""

from __future__ import annotations

import argparse
import copy
import dataclasses
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional, Sequence
from zoneinfo import ZoneInfo


AUTO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTO_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(
    0,
    str(REPO_ROOT / "CodexSkills" / "governance" / "tools"),
)

from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    CanonicalizationError,
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_mechanism import (  # noqa: E402
    ContractBundle,
    ContractError,
    TrustTuple,
    build_registry,
    load_schema_directories,
    scan_public_value,
    strict_load,
    validate_instance,
)
from CodexSkills.registry.auto.tools.build_transport_draft import (  # noqa: E402
    CURRENT_CANDIDATE_BUNDLE_DIGEST,
    CURRENT_CANDIDATE_GIT_OBJECT,
    CURRENT_CANDIDATE_MANIFEST_PATH,
    DAILY_MANIFEST_ID,
    DRAFT_DIR,
    INDEX_ENTRY_ID,
    JSONL_SERIALIZATION,
    MAX_PART_BYTES,
    OBJECT_SERIALIZATION,
    OUTPUT_INTERFACE,
    PUBLICATION_V1_ID,
    PUBLICATION_V2_ID,
    PUBLIC_RUN_EVENT_ID,
    REQUIRED_MECHANISM_PUBLIC_VALUE_ALLOWLIST_ADDITIONS,
    RETENTION_V2_ID,
    RETENTION_V3_ID,
    RUN_LOG_ROOT,
    SCHEMA_DIR,
    SELF_POINTERS,
)
from CodexSkills.registry.auto.tools.validate_auto import (  # noqa: E402
    load_trusted_auto_contract,
)


PUBLIC_VALUE_POLICY_ID = (
    "urn:linzecolin:agentdatabase:skillops:policy:public-value:v1"
)
RETENTION_POLICY_V3_ID = (
    "urn:linzecolin:agentdatabase:skillops:policy:retention:v3"
)
SHARED_GATES = (
    "BUNDLE_DIGEST",
    "EXPECTED_REMOTE_HEAD",
    "LOCK_OWNERSHIP",
    "PATH_BOUNDARY",
    "POLICY_DIGEST",
    "PRIVACY",
)
REGISTRY_WRITE_PREFIXES = (
    "CodexSkills/governance/",
    "CodexSkills/registry/",
    "CodexSkills/skill_controlled_iterate/",
    "CodexSkills/skill_log_evals/",
)
REGISTRY_CONTROL_PATHS = {
    "CodexSkills/CHANGELOG.md",
    "CodexSkills/HANDOFF.md",
    "CodexSkills/VERSION",
}
DAILY_PATH_RE = re.compile(
    r"^OpenAIDatabase/data/run_logs/skills_runs/"
    r"([0-9]{4})/([0-9]{2})/([0-9]{2})/"
    r"(manifest|index|part)-([0-9]{4})\.(json|jsonl)$"
)
PUBLIC_BLOCK_PATH_RE = re.compile(
    r"PUBLIC_HIGH_ENTROPY_FREE_STRING_BLOCK:\$.*[/\\.]"
    r"(?P<field>[a-z][a-z0-9_]*)$"
)


@dataclasses.dataclass(frozen=True)
class TransportDraftContract:
    bundle: ContractBundle
    interface: Mapping[str, Any]
    current_candidate: ContractBundle


def _fail(code: str) -> None:
    raise ContractError(code)


def _parse_utc(value: str) -> dt.datetime:
    try:
        return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=dt.timezone.utc
        )
    except (TypeError, ValueError) as exc:
        raise ContractError(f"AUTO_TRANSPORT_UTC_INVALID:{value}") from exc


def _require_sorted_unique(
    values: Sequence[Any],
    key,
    code: str,
) -> None:
    keys = [key(item) for item in values]
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        _fail(f"{code}:SORTED_UNIQUE_REQUIRED")


def _policy_with_allowlist_delta(
    policies: Mapping[str, Any],
    additions: Iterable[str],
) -> Mapping[str, Any]:
    copied = copy.deepcopy(dict(policies))
    policy = copied.get(PUBLIC_VALUE_POLICY_ID)
    if not isinstance(policy, dict):
        _fail("AUTO_TRANSPORT_PUBLIC_VALUE_POLICY_MISSING")
    allowed = set(policy["allowed_high_entropy_field_names"])
    allowed.update(additions)
    policy["allowed_high_entropy_field_names"] = sorted(allowed)
    return copied


def load_transport_draft() -> TransportDraftContract:
    """Compose 31 proposed schemas without mutating the trusted 29/5 tuple."""

    trust = TrustTuple(
        CURRENT_CANDIDATE_GIT_OBJECT,
        CURRENT_CANDIDATE_BUNDLE_DIGEST,
        CURRENT_CANDIDATE_MANIFEST_PATH,
        "CANDIDATE",
    )
    current = load_trusted_auto_contract(REPO_ROOT, trust).shared
    if len(current.schemas) != 29 or len(current.policies) != 5:
        _fail("AUTO_TRANSPORT_CURRENT_CANDIDATE_NOT_29_5")

    draft_schemas = load_schema_directories([SCHEMA_DIR])
    if set(draft_schemas) != set(SELF_POINTERS):
        _fail("AUTO_TRANSPORT_DRAFT_SCHEMA_SET_MISMATCH")
    interface = strict_load(OUTPUT_INTERFACE)
    entries = interface.get("draft_schema_entries")
    if (
        interface.get("status") != "DRAFT_NON_ACTIVE"
        or interface.get("activation_forbidden") is not True
        or interface.get("repository_bound") is not False
        or interface.get("au_040_complete") is not False
        or interface.get("canonical_publication_permitted") is not False
        or not isinstance(entries, list)
        or len(entries) != 4
    ):
        _fail("AUTO_TRANSPORT_DRAFT_INTERFACE_STATE_INVALID")
    entry_ids = [entry.get("id") for entry in entries]
    if entry_ids != sorted(SELF_POINTERS) or set(entry_ids) != set(SELF_POINTERS):
        _fail("AUTO_TRANSPORT_DRAFT_INTERFACE_ENTRY_SET_INVALID")
    for entry in entries:
        schema_id = entry["id"]
        expected_path = (
            SCHEMA_DIR
            / next(
                path.name
                for path in SCHEMA_DIR.glob("*.json")
                if strict_load(path).get("$id") == schema_id
            )
        )
        if entry.get("draft_relative_path") != expected_path.relative_to(
            REPO_ROOT
        ).as_posix():
            _fail(f"AUTO_TRANSPORT_DRAFT_SCHEMA_PATH_INVALID:{schema_id}")
        proposed = entry.get("proposed_canonical_relative_path")
        expected_proposed = (
            "CodexSkills/registry/auto/schemas/public-v2/"
            + expected_path.name
        )
        if (
            proposed != expected_proposed
            or "draft" in proposed.split("/")
            or proposed.startswith(
                "CodexSkills/registry/auto/schemas/public/"
            )
        ):
            _fail(
                f"AUTO_TRANSPORT_PROPOSED_CANONICAL_PATH_INVALID:{schema_id}"
            )
        observed = hashlib.sha256(
            canonicalize_object(draft_schemas[schema_id])
        ).hexdigest()
        if (
            entry.get("schema_sha256") != observed
            or entry.get("self_digest_pointer") != SELF_POINTERS[schema_id]
        ):
            _fail(f"AUTO_TRANSPORT_DRAFT_SCHEMA_EVIDENCE_INVALID:{schema_id}")

    target_schemas = dict(current.schemas)
    target_pointers = dict(current.self_digest_pointers)
    for schema_id in (PUBLICATION_V1_ID, RETENTION_V2_ID):
        if schema_id not in target_schemas:
            _fail(f"AUTO_TRANSPORT_REPLACED_SCHEMA_MISSING:{schema_id}")
        del target_schemas[schema_id]
        target_pointers.pop(schema_id, None)
    target_schemas.update(draft_schemas)
    target_pointers.update(SELF_POINTERS)
    if len(target_schemas) != 31:
        _fail("AUTO_TRANSPORT_TARGET_SCHEMA_COUNT_NOT_31")
    loader = interface.get("loader_isolation_invariant")
    validation_context = interface.get("draft_validation_context")
    target = interface.get("proposed_active_shared_set")
    if (
        interface.get("promotion_required_before_candidate_materialization")
        is not True
        or interface.get("draft_paths_forbidden_in_candidate_manifest")
        is not True
        or interface.get("next_phase")
        != "MECHANISM_AU040_SEMANTIC_POLICY_ACCEPTANCE"
        or not isinstance(loader, dict)
        or loader.get("current_candidate_recursive_loader_root")
        != "CodexSkills/registry/auto/schemas/public/"
        or loader.get("proposed_canonical_root")
        != "CodexSkills/registry/auto/schemas/public-v2/"
        or loader.get("proposed_paths_visible_to_current_loader") is not False
        or not isinstance(validation_context, dict)
        or validation_context.get("retention_policy_v3_present") is not False
        or validation_context.get(
            "current_policy_set_used_for_schema_validation_only"
        )
        is not True
        or validation_context.get("mechanism_policy_acceptance_required")
        is not True
        or not isinstance(target, dict)
        or target.get("replaced_policy_ids")
        != ["urn:linzecolin:agentdatabase:skillops:policy:retention:v2"]
        or target.get("replacement_policy_ids")
        != ["urn:linzecolin:agentdatabase:skillops:policy:retention:v3"]
    ):
        _fail("AUTO_TRANSPORT_PROMOTION_SEQUENCE_GUARD_INVALID")
    registry, format_checker = build_registry(target_schemas)
    bundle = ContractBundle(
        target_schemas,
        registry,
        format_checker,
        target_pointers,
        current.policies,
        current.protocol_revision,
    )
    return TransportDraftContract(bundle, interface, current)


def _sydney_date(value: str) -> str:
    return _parse_utc(value).astimezone(ZoneInfo("Australia/Sydney")).date().isoformat()


def _validate_daily_manifest(instance: Mapping[str, Any]) -> None:
    parts = instance["parts"]
    numbers = [part["part_number"] for part in parts]
    if numbers != list(range(1, len(parts) + 1)) or numbers[-1] > 9999:
        _fail("DAILY_MANIFEST_PART_NUMBERS_NOT_CONTIGUOUS")
    if instance["manifest_revision"] > 9999:
        _fail("DAILY_MANIFEST_REVISION_EXCEEDS_PATH_WIDTH")
    if instance["max_part_number"] != numbers[-1]:
        _fail("DAILY_MANIFEST_MAX_PART_NUMBER_MISMATCH")
    if instance["total_part_count"] != len(parts):
        _fail("DAILY_MANIFEST_TOTAL_PART_COUNT_MISMATCH")

    active = [part for part in parts if part["state"] == "ACTIVE"]
    pruned = [part for part in parts if part["state"] == "PRUNED"]
    if instance["active_part_count"] != len(active):
        _fail("DAILY_MANIFEST_ACTIVE_PART_COUNT_MISMATCH")
    if instance["pruned_part_count"] != len(pruned):
        _fail("DAILY_MANIFEST_PRUNED_PART_COUNT_MISMATCH")
    if len(active) + len(pruned) != len(parts):
        _fail("DAILY_MANIFEST_STATE_COUNT_MISMATCH")
    if instance["active_shard_bytes"] != sum(
        part["shard_bytes"] for part in active
    ):
        _fail("DAILY_MANIFEST_ACTIVE_BYTES_MISMATCH")
    if instance["active_record_count"] != sum(
        part["record_count"] for part in active
    ):
        _fail("DAILY_MANIFEST_ACTIVE_RECORDS_MISMATCH")
    if instance["retained_index_bytes"] != sum(
        part["index_bytes"] for part in parts
    ):
        _fail("DAILY_MANIFEST_RETAINED_INDEX_BYTES_MISMATCH")
    if instance["retained_index_record_count"] != sum(
        part["index_record_count"] for part in parts
    ):
        _fail("DAILY_MANIFEST_RETAINED_INDEX_RECORDS_MISMATCH")

    publication_at = _parse_utc(instance["publication_transaction_at"])
    for part in parts:
        number = part["part_number"]
        if part["shard_name"] != f"part-{number:04d}.jsonl":
            _fail("DAILY_MANIFEST_SHARD_NAME_NUMBER_MISMATCH")
        if part["index_name"] != f"index-{number:04d}.jsonl":
            _fail("DAILY_MANIFEST_INDEX_NAME_NUMBER_MISMATCH")
        if part["shard_bytes"] > MAX_PART_BYTES:
            _fail("DAILY_MANIFEST_SHARD_SIZE_EXCEEDED")
        if part["record_count"] != part["index_record_count"]:
            _fail("DAILY_MANIFEST_INDEX_RECORD_COUNT_MISMATCH")
        first_key = (_parse_utc(part["first_occurred_at"]), part["first_event_uid"])
        last_key = (_parse_utc(part["last_occurred_at"]), part["last_event_uid"])
        if first_key > last_key:
            _fail("DAILY_MANIFEST_EVENT_RANGE_REVERSED")
        if (
            _sydney_date(part["first_occurred_at"]) != instance["local_date"]
            or _sydney_date(part["last_occurred_at"]) != instance["local_date"]
        ):
            _fail("DAILY_MANIFEST_SYDNEY_DATE_MISMATCH")
        first_published = _parse_utc(part["first_published_at"])
        retention_anchor = _parse_utc(part["retention_not_before"])
        if first_published < last_key[0]:
            _fail("DAILY_MANIFEST_PUBLISHED_BEFORE_EVENT")
        if publication_at < first_published:
            _fail("DAILY_MANIFEST_REVISION_BEFORE_FIRST_PUBLICATION")
        if retention_anchor <= first_published:
            _fail("DAILY_MANIFEST_RETENTION_ANCHOR_NOT_AFTER_PUBLICATION")
        if part["state"] == "PRUNED":
            pruned_at = _parse_utc(part["pruned_at"])
            if pruned_at <= retention_anchor:
                _fail("DAILY_MANIFEST_PRUNE_NOT_STRICTLY_AFTER_ANCHOR")
            if pruned_at > publication_at:
                _fail("DAILY_MANIFEST_PRUNE_AFTER_REVISION_PUBLICATION")


def validate_manifest_tree(
    instance: Mapping[str, Any],
    manifest_repo_path: str,
    artifacts: Mapping[str, Mapping[str, Any]],
) -> None:
    """Validate logical active-tree closure without writing repository data."""

    match = DAILY_PATH_RE.fullmatch(manifest_repo_path)
    if (
        match is None
        or match.group(4) != "manifest"
        or match.group(6) != "json"
        or int(match.group(5)) != instance["manifest_revision"]
    ):
        _fail("DAILY_MANIFEST_REPO_PATH_INVALID")
    local_date = "-".join(match.group(index) for index in (1, 2, 3))
    if local_date != instance["local_date"]:
        _fail("DAILY_MANIFEST_REPO_PATH_DATE_MISMATCH")
    prefix = manifest_repo_path.rsplit("/", 1)[0] + "/"
    expected_paths = set()
    for part in instance["parts"]:
        shard_path = prefix + part["shard_name"]
        index_path = prefix + part["index_name"]
        expected_paths.add(index_path)
        index = artifacts.get(index_path)
        if index is None:
            _fail(f"DAILY_MANIFEST_RETAINED_INDEX_MISSING:{index_path}")
        if (
            index.get("digest") != part["index_digest"]
            or index.get("bytes") != part["index_bytes"]
            or index.get("records") != part["index_record_count"]
        ):
            _fail(f"DAILY_MANIFEST_RETAINED_INDEX_MISMATCH:{index_path}")
        shard = artifacts.get(shard_path)
        if part["state"] == "ACTIVE":
            expected_paths.add(shard_path)
            if shard is None:
                _fail(f"DAILY_MANIFEST_ACTIVE_SHARD_MISSING:{shard_path}")
            if (
                shard.get("digest") != part["shard_digest"]
                or shard.get("bytes") != part["shard_bytes"]
                or shard.get("records") != part["record_count"]
            ):
                _fail(f"DAILY_MANIFEST_ACTIVE_SHARD_MISMATCH:{shard_path}")
        elif shard is not None:
            _fail(f"DAILY_MANIFEST_PRUNED_SHARD_PRESENT:{shard_path}")
    observed_run_files = {
        path
        for path in artifacts
        if path.startswith(prefix)
        and (
            path.rsplit("/", 1)[-1].startswith("part-")
            or path.rsplit("/", 1)[-1].startswith("index-")
        )
    }
    if observed_run_files != expected_paths:
        _fail("DAILY_MANIFEST_TREE_HAS_UNLISTED_RUN_ARTIFACT")


def validate_pruned_manifest_receipt_links(
    instance: Mapping[str, Any],
    manifest_repo_path: str,
    receipts: Mapping[str, Mapping[str, Any]],
) -> None:
    """Bind each PRUNED manifest entry to its exact prior-tree receipt."""

    if instance["manifest_revision"] == 1 and any(
        part["state"] == "PRUNED" for part in instance["parts"]
    ):
        _fail("DAILY_MANIFEST_REVISION_ONE_CANNOT_CONTAIN_PRUNED_PART")
    prior_manifest_digest = instance["previous_manifest_digest"]
    prefix = manifest_repo_path.rsplit("/", 1)[0] + "/"
    for part in instance["parts"]:
        if part["state"] != "PRUNED":
            continue
        receipt_path = part["retention_receipt_path"]
        receipt = receipts.get(receipt_path)
        if receipt is None:
            _fail(f"DAILY_MANIFEST_RETENTION_RECEIPT_MISSING:{receipt_path}")
        if (
            receipt.get("receipt_uid") != part["retention_receipt_uid"]
            or receipt.get("receipt_digest")
            != part["retention_receipt_digest"]
            or receipt.get("executed_at") != part["pruned_at"]
        ):
            _fail("DAILY_MANIFEST_RETENTION_RECEIPT_IDENTITY_MISMATCH")
        shard_path = prefix + part["shard_name"]
        affected = [
            item
            for item in receipt.get("affected_public_artifacts", [])
            if item.get("artifact_repo_path") == shard_path
        ]
        if len(affected) != 1:
            _fail("DAILY_MANIFEST_RETENTION_AFFECTED_PART_NOT_EXACT")
        item = affected[0]
        expected = {
            "prior_artifact_digest": part["shard_digest"],
            "prior_artifact_bytes": part["shard_bytes"],
            "prior_record_count": part["record_count"],
            "first_published_at": part["first_published_at"],
            "retention_not_before": part["retention_not_before"],
            "retained_index_path": prefix + part["index_name"],
            "retained_index_digest": part["index_digest"],
            "prior_daily_manifest_digest": prior_manifest_digest,
        }
        if any(item.get(key) != value for key, value in expected.items()):
            _fail("DAILY_MANIFEST_RETENTION_AFFECTED_PART_MISMATCH")


def _validate_index_entry(instance: Mapping[str, Any]) -> None:
    if _parse_utc(instance["first_published_at"]) < _parse_utc(
        instance["occurred_at"]
    ):
        _fail("RUN_EVENT_INDEX_PUBLISHED_BEFORE_OCCURRED")
    if instance["event_type"] == "BINDING_CORRECTION":
        if (
            instance["event_uid"] == instance["supersedes_event_uid"]
            or instance["event_digest"] == instance["supersedes_event_digest"]
        ):
            _fail("RUN_EVENT_INDEX_CORRECTION_SELF_REFERENCE")


def validate_index_entries(
    entries: Sequence[Mapping[str, Any]],
    *,
    event_rows: Sequence[Mapping[str, Any]],
    expected_part_number: int,
    expected_record_count: int,
    known_events: Optional[Mapping[str, str]] = None,
) -> None:
    if len(entries) != expected_record_count:
        _fail("RUN_EVENT_INDEX_RECORD_COUNT_MISMATCH")
    if [entry["line_number"] for entry in entries] != list(
        range(1, len(entries) + 1)
    ):
        _fail("RUN_EVENT_INDEX_LINE_NUMBERS_NOT_CONTIGUOUS")
    if any(entry["part_number"] != expected_part_number for entry in entries):
        _fail("RUN_EVENT_INDEX_PART_NUMBER_MISMATCH")
    ordering = [(entry["occurred_at"], entry["event_uid"]) for entry in entries]
    if ordering != sorted(ordering) or len(ordering) != len(set(ordering)):
        _fail("RUN_EVENT_INDEX_ORDER_INVALID")
    if len({entry["event_uid"] for entry in entries}) != len(entries):
        _fail("RUN_EVENT_INDEX_EVENT_UID_DUPLICATE")
    if len(event_rows) != len(entries):
        _fail("RUN_EVENT_INDEX_EVENT_ROW_COUNT_MISMATCH")
    compared_fields = (
        "event_uid",
        "event_digest",
        "event_type",
        "occurred_at",
    )
    correction_fields = (
        "supersedes_event_uid",
        "supersedes_event_digest",
    )
    for entry, event in zip(entries, event_rows):
        if any(entry.get(field) != event.get(field) for field in compared_fields):
            _fail("RUN_EVENT_INDEX_EVENT_ROW_MISMATCH")
        if any(
            entry.get(field) != event.get(field)
            for field in correction_fields
        ):
            _fail("RUN_EVENT_INDEX_CORRECTION_ROW_MISMATCH")
    observed: MutableMapping[str, str] = dict(known_events or {})
    for entry in entries:
        if entry["event_type"] == "BINDING_CORRECTION":
            target_uid = entry["supersedes_event_uid"]
            target_digest = entry["supersedes_event_digest"]
            if observed.get(target_uid) != target_digest:
                _fail("RUN_EVENT_INDEX_CORRECTION_TARGET_NOT_EXACT")
        existing = observed.get(entry["event_uid"])
        if existing is not None and existing != entry["event_digest"]:
            _fail("RUN_EVENT_INDEX_DEDUPE_DIGEST_CONFLICT")
        observed[entry["event_uid"]] = entry["event_digest"]


def _parse_daily_path(path: str) -> tuple[str, str, int]:
    match = DAILY_PATH_RE.fullmatch(path)
    if match is None:
        _fail(f"PUBLICATION_RUN_LOG_PATH_INVALID:{path}")
    try:
        date = dt.date(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
        )
    except ValueError as exc:
        raise ContractError(f"PUBLICATION_RUN_LOG_DATE_INVALID:{path}") from exc
    if date.isoformat() != "-".join(match.group(index) for index in (1, 2, 3)):
        _fail(f"PUBLICATION_RUN_LOG_DATE_NONCANONICAL:{path}")
    kind = match.group(4)
    number = int(match.group(5))
    extension = match.group(6)
    if number < 1 or number > 9999:
        _fail(f"PUBLICATION_RUN_LOG_SEQUENCE_INVALID:{path}")
    if (kind == "manifest") != (extension == "json"):
        _fail(f"PUBLICATION_RUN_LOG_EXTENSION_INVALID:{path}")
    return kind, extension, number


def _validate_publication_artifact(
    bundle: ContractBundle,
    lane: str,
    artifact: Mapping[str, Any],
) -> None:
    path = artifact["artifact_repo_path"]
    operation = artifact["artifact_operation"]
    if lane == "REGISTRY":
        if operation != "PUT":
            _fail(f"PUBLICATION_UNLISTED_DELETION:{path}")
        if not (
            path in REGISTRY_CONTROL_PATHS
            or any(path.startswith(prefix) for prefix in REGISTRY_WRITE_PREFIXES)
        ):
            _fail(f"PUBLICATION_REGISTRY_PATH_INVALID:{path}")
        if artifact["artifact_serialization"] != OBJECT_SERIALIZATION:
            _fail("PUBLICATION_REGISTRY_SERIALIZATION_INVALID")
        if artifact["artifact_schema_id"] not in bundle.schemas:
            _fail("PUBLICATION_REGISTRY_SCHEMA_UNKNOWN")
        return

    kind, _, _ = _parse_daily_path(path)
    serialization_field = (
        "artifact_serialization"
        if operation == "PUT"
        else "prior_artifact_serialization"
    )
    serialization = artifact[serialization_field]
    schema_id = artifact["artifact_schema_id"]
    if kind == "part":
        if schema_id != PUBLIC_RUN_EVENT_ID or serialization != JSONL_SERIALIZATION:
            _fail("PUBLICATION_PART_PATH_OPERATION_SCHEMA_MISMATCH")
        return
    if operation == "DELETE":
        _fail(f"PUBLICATION_UNLISTED_DELETION:{path}")
    if kind == "index":
        if schema_id != INDEX_ENTRY_ID or serialization != JSONL_SERIALIZATION:
            _fail("PUBLICATION_INDEX_PATH_OPERATION_SCHEMA_MISMATCH")
        return
    if (
        schema_id != DAILY_MANIFEST_ID
        or serialization != OBJECT_SERIALIZATION
    ):
        _fail("PUBLICATION_MANIFEST_PATH_OPERATION_SCHEMA_MISMATCH")


def _validate_publication_manifest(
    instance: Mapping[str, Any],
    bundle: ContractBundle,
) -> None:
    lanes = instance["lane_manifests"]
    _require_sorted_unique(lanes, lambda item: item["lane"], "PUBLICATION_LANE_ORDER")
    if instance["settled_lanes"] != [item["lane"] for item in lanes]:
        _fail("PUBLICATION_SETTLED_LANE_MISMATCH")
    all_uids = []
    all_paths = []
    for lane in lanes:
        artifacts = lane["artifacts"]
        if lane["artifact_count"] != len(artifacts):
            _fail("PUBLICATION_ARTIFACT_COUNT_MISMATCH")
        _require_sorted_unique(
            artifacts,
            lambda item: (item["artifact_repo_path"], item["artifact_uid"]),
            "PUBLICATION_ARTIFACT_ORDER",
        )
        for artifact in artifacts:
            all_uids.append(artifact["artifact_uid"])
            all_paths.append(artifact["artifact_repo_path"])
            _validate_publication_artifact(bundle, lane["lane"], artifact)
    if len(all_uids) != len(set(all_uids)):
        _fail("PUBLICATION_ARTIFACT_UID_DUPLICATE")
    if len(all_paths) != len(set(all_paths)):
        _fail("PUBLICATION_PATH_OPERATION_COLLISION")
    gates = instance["shared_gates"]
    _require_sorted_unique(gates, lambda item: item["gate_code"], "PUBLICATION_GATE_ORDER")
    if tuple(item["gate_code"] for item in gates) != SHARED_GATES:
        _fail("PUBLICATION_SHARED_GATE_SET_INCOMPLETE")


def _validate_retention_receipt(instance: Mapping[str, Any]) -> None:
    executed_at = _parse_utc(instance["executed_at"])
    if executed_at < _parse_utc(instance["cutoff_at"]):
        _fail("RETENTION_CUTOFF_AFTER_EXECUTION")
    if instance["affected_count"] > instance["selected_count"]:
        _fail("RETENTION_AFFECTED_COUNT_EXCEEDS_SELECTED")
    if instance["affected_bytes"] > instance["selected_bytes"]:
        _fail("RETENTION_AFFECTED_BYTES_EXCEED_SELECTED")
    if instance["action"] in {"KEEP", "NO_CANDIDATE"} and (
        instance["affected_count"] or instance["affected_bytes"]
    ):
        _fail("RETENTION_NON_MUTATING_ACTION_HAS_EFFECT")
    if instance["action"] == "NO_CANDIDATE" and (
        instance["selected_count"] or instance["selected_bytes"]
    ):
        _fail("RETENTION_NO_CANDIDATE_SELECTED_NONZERO")

    affected = instance.get("affected_public_artifacts", [])
    if (
        instance["scope"] == "GIT_CURRENT_TREE"
        and instance["action"] == "PRUNE_CURRENT_TREE"
    ):
        _require_sorted_unique(
            affected,
            lambda item: item["artifact_repo_path"],
            "RETENTION_AFFECTED_ARTIFACT_ORDER",
        )
        if instance["affected_count"] != len(affected):
            _fail("RETENTION_AFFECTED_ARTIFACT_COUNT_MISMATCH")
        if instance["affected_bytes"] != sum(
            item["prior_artifact_bytes"] for item in affected
        ):
            _fail("RETENTION_AFFECTED_ARTIFACT_BYTES_MISMATCH")
        deadline_breached = False
        for item in affected:
            kind, _, number = _parse_daily_path(item["artifact_repo_path"])
            if kind != "part":
                _fail("RETENTION_AFFECTED_ARTIFACT_NOT_PART")
            index_kind, _, index_number = _parse_daily_path(
                item["retained_index_path"]
            )
            if index_kind != "index" or index_number != number:
                _fail("RETENTION_RETAINED_INDEX_PAIR_MISMATCH")
            if item["artifact_repo_path"].rsplit("/", 1)[0] != item[
                "retained_index_path"
            ].rsplit("/", 1)[0]:
                _fail("RETENTION_RETAINED_INDEX_DATE_MISMATCH")
            first_published = _parse_utc(item["first_published_at"])
            anchor = _parse_utc(item["retention_not_before"])
            deadline = _parse_utc(item["prune_deadline_at"])
            if anchor <= first_published:
                _fail("RETENTION_ANCHOR_NOT_AFTER_FIRST_PUBLICATION")
            if deadline != anchor + dt.timedelta(hours=24):
                _fail("RETENTION_PRUNE_DEADLINE_NOT_24H_AFTER_ANCHOR")
            if executed_at <= anchor:
                _fail("RETENTION_EXECUTION_NOT_STRICTLY_AFTER_ANCHOR")
            if executed_at > deadline:
                deadline_breached = True
        if instance["prune_deadline_breached"] is not deadline_breached:
            _fail("RETENTION_PRUNE_DEADLINE_BREACH_STATE_MISMATCH")
        if deadline_breached:
            if (
                instance.get("gap_code")
                != "GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH"
            ):
                _fail("RETENTION_PRUNE_DEADLINE_BREACH_GAP_REQUIRED")
        elif "gap_code" in instance:
            _fail("RETENTION_ON_TIME_PRUNE_GAP_FORBIDDEN")
    elif affected:
        _fail("RETENTION_PUBLIC_DETAILS_OUTSIDE_ACTIVE_TREE_PRUNE")
    elif (
        instance["scope"] == "GIT_CURRENT_TREE"
        and "gap_code" in instance
    ):
        _fail("RETENTION_GIT_GAP_OUTSIDE_PRUNE_FORBIDDEN")
    if (
        instance["scope"] == "MANAGED_RAW"
        and instance.get("gap_code")
        == "GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH"
    ):
        _fail("RETENTION_GIT_DEADLINE_GAP_ON_MANAGED_RAW")

    if instance["ttl_breach"]:
        if (
            instance.get("gap_code") != "OFFLINE_TTL_BREACH"
            or instance["offline_duration_seconds"] == 0
            or instance["action"] != "OFFLINE_TTL_BREACH_CLEANUP"
        ):
            _fail("RETENTION_TTL_BREACH_EVIDENCE_INCOMPLETE")
    elif instance.get("gap_code") == "OFFLINE_TTL_BREACH":
        _fail("RETENTION_OFFLINE_GAP_WITHOUT_TTL_BREACH")
    if (
        instance["reprojection_status"] == "FAILED_GAP_RECORDED"
        and "gap_code" not in instance
    ):
        _fail("RETENTION_FAILED_REPROJECTION_GAP_CODE_REQUIRED")


def validate_transport_instance(
    contract: TransportDraftContract,
    instance: Any,
    schema_id: str,
    *,
    expected_bundle_digest: str,
    allow_draft_policy_delta: bool = False,
    verify_digest: bool = True,
) -> None:
    if schema_id not in SELF_POINTERS:
        _fail(f"AUTO_TRANSPORT_SCHEMA_ID_UNKNOWN:{schema_id}")
    validate_instance(
        contract.bundle,
        instance,
        schema_id,
        expected_bundle_digest=expected_bundle_digest,
        public=False,
        verify_digest=verify_digest,
    )
    if schema_id == DAILY_MANIFEST_ID:
        _validate_daily_manifest(instance)
    elif schema_id == INDEX_ENTRY_ID:
        _validate_index_entry(instance)
    elif schema_id == PUBLICATION_V2_ID:
        _validate_publication_manifest(instance, contract.bundle)
    elif schema_id == RETENTION_V3_ID:
        _validate_retention_receipt(instance)
    policies = contract.bundle.policies
    if allow_draft_policy_delta:
        policies = _policy_with_allowlist_delta(
            policies,
            REQUIRED_MECHANISM_PUBLIC_VALUE_ALLOWLIST_ADDITIONS,
        )
    scan_public_value(instance, policies)


def validate_jcs_object_bytes(
    raw: bytes,
    contract: TransportDraftContract,
    schema_id: str,
    *,
    expected_bundle_digest: str,
    allow_draft_policy_delta: bool = False,
) -> Mapping[str, Any]:
    instance = parse_json_bytes(raw)
    if not isinstance(instance, dict):
        _fail("AUTO_TRANSPORT_JCS_ROOT_NOT_OBJECT")
    if canonicalize_object(instance) != raw:
        _fail("AUTO_TRANSPORT_JCS_BYTES_NOT_CANONICAL")
    validate_transport_instance(
        contract,
        instance,
        schema_id,
        expected_bundle_digest=expected_bundle_digest,
        allow_draft_policy_delta=allow_draft_policy_delta,
    )
    return instance


def validate_jcs_jsonl_bytes(
    raw: bytes,
    contract: TransportDraftContract,
    schema_id: str,
    *,
    expected_bundle_digest: str,
    allow_draft_policy_delta: bool = False,
    max_bytes: int = MAX_PART_BYTES,
) -> list[Mapping[str, Any]]:
    if (
        not raw
        or len(raw) > max_bytes
        or not raw.endswith(b"\n")
        or b"\r" in raw
    ):
        _fail("AUTO_TRANSPORT_JSONL_FRAMING_INVALID")
    if raw.startswith(b"\xef\xbb\xbf"):
        _fail("AUTO_TRANSPORT_JSONL_BOM_FORBIDDEN")
    rows = []
    for line_number, line in enumerate(raw[:-1].split(b"\n"), 1):
        if not line:
            _fail(f"AUTO_TRANSPORT_JSONL_EMPTY_LINE:{line_number}")
        try:
            instance = parse_json_bytes(line)
            canonical = canonicalize_object(instance)
        except CanonicalizationError as exc:
            raise ContractError(
                f"AUTO_TRANSPORT_JSONL_LINE_NOT_JCS:{line_number}:{exc}"
            ) from exc
        if not isinstance(instance, dict) or canonical != line:
            _fail(f"AUTO_TRANSPORT_JSONL_LINE_NOT_JCS:{line_number}")
        validate_transport_instance(
            contract,
            instance,
            schema_id,
            expected_bundle_digest=expected_bundle_digest,
            allow_draft_policy_delta=allow_draft_policy_delta,
        )
        rows.append(instance)
    return rows


def discover_required_allowlist_additions(
    fixtures: Sequence[Mapping[str, Any]],
    policies: Mapping[str, Any],
) -> list[str]:
    """Run the current scanner, then minimally unblock each exact field name."""

    discovered = set()
    for fixture in fixtures:
        additions = set()
        while True:
            candidate_policies = _policy_with_allowlist_delta(
                policies,
                additions,
            )
            try:
                scan_public_value(fixture, candidate_policies)
                break
            except ContractError as exc:
                match = PUBLIC_BLOCK_PATH_RE.fullmatch(str(exc))
                if match is None:
                    raise
                field = match.group("field")
                if field in additions:
                    raise
                additions.add(field)
        discovered.update(additions)
    return sorted(discovered)


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _uid(prefix: str, digit: str) -> str:
    return prefix + "_" + digit + ("1" * 25)


def _finalize(instance: Dict[str, Any], pointer: str) -> Dict[str, Any]:
    field = pointer.removeprefix("/")
    instance[field] = "0" * 64
    instance[field] = canonical_digest(instance, pointer)
    return instance


def daily_manifest_fixture() -> Dict[str, Any]:
    retention_receipt = retention_receipt_fixture()
    parts = [
        {
            "part_number": 1,
            "shard_name": "part-0001.jsonl",
            "state": "ACTIVE",
            "shard_digest": _digest("shard-1"),
            "shard_bytes": 2048,
            "record_count": 2,
            "index_name": "index-0001.jsonl",
            "index_digest": _digest("index-1"),
            "index_bytes": 1024,
            "index_record_count": 2,
            "first_event_uid": _uid("evt", "1"),
            "first_event_digest": _digest("event-1"),
            "first_occurred_at": "2026-07-22T14:00:00.000000Z",
            "last_event_uid": _uid("evt", "2"),
            "last_event_digest": _digest("event-2"),
            "last_occurred_at": "2026-07-22T15:00:00.000000Z",
            "first_published_at": "2026-07-22T16:00:00.000000Z",
            "retention_not_before": "2027-07-22T16:00:00.000000Z",
        },
        {
            "part_number": 2,
            "shard_name": "part-0002.jsonl",
            "state": "PRUNED",
            "shard_digest": _digest("shard-2"),
            "shard_bytes": 4096,
            "record_count": 3,
            "index_name": "index-0002.jsonl",
            "index_digest": _digest("index-2"),
            "index_bytes": 1536,
            "index_record_count": 3,
            "first_event_uid": _uid("evt", "3"),
            "first_event_digest": _digest("event-3"),
            "first_occurred_at": "2026-07-22T15:30:00.000000Z",
            "last_event_uid": _uid("evt", "4"),
            "last_event_digest": _digest("event-4"),
            "last_occurred_at": "2026-07-22T16:30:00.000000Z",
            "first_published_at": "2026-07-22T17:00:00.000000Z",
            "retention_not_before": "2027-07-22T17:00:00.000000Z",
            "retention_receipt_path": (
                "OpenAIDatabase/data/run_logs/skills_runs/"
                "2026/07/23/retention-receipt-0001.json"
            ),
            "retention_receipt_uid": retention_receipt["receipt_uid"],
            "retention_receipt_digest": retention_receipt["receipt_digest"],
            "pruned_at": retention_receipt["executed_at"],
        },
    ]
    return _finalize(
        {
            "schema_version": DAILY_MANIFEST_ID,
            "protocol_revision": (
                "urn:linzecolin:agentdatabase:skillops:"
                "protocol:cross-pack:v1"
            ),
            "bundle_digest": CURRENT_CANDIDATE_BUNDLE_DIGEST,
            "manifest_uid": _uid("drm", "1"),
            "local_date": "2026-07-23",
            "timezone": "Australia/Sydney",
            "record_schema_id": PUBLIC_RUN_EVENT_ID,
            "artifact_serialization": JSONL_SERIALIZATION,
            "max_part_bytes": MAX_PART_BYTES,
            "manifest_revision": 2,
            "previous_manifest_digest": _digest("daily-before-prune"),
            "auto_transaction_uid": _uid("atx", "2"),
            "publication_transaction_at": "2027-07-22T19:00:00.000000Z",
            "max_part_number": 2,
            "total_part_count": 2,
            "active_part_count": 1,
            "pruned_part_count": 1,
            "active_shard_bytes": 2048,
            "active_record_count": 2,
            "retained_index_bytes": 2560,
            "retained_index_record_count": 5,
            "parts": parts,
        },
        "/manifest_digest",
    )


def index_entry_fixture(*, correction: bool = False) -> Dict[str, Any]:
    event_number = "7" if correction else "6"
    instance: Dict[str, Any] = {
        "schema_version": INDEX_ENTRY_ID,
        "protocol_revision": (
            "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
        ),
        "bundle_digest": CURRENT_CANDIDATE_BUNDLE_DIGEST,
        "event_uid": _uid("evt", event_number),
        "event_digest": _digest("indexed-event-" + event_number),
        "event_type": "BINDING_CORRECTION" if correction else "RUN_OBSERVED",
        "occurred_at": (
            "2026-07-22T15:00:00.000000Z"
            if correction
            else "2026-07-22T14:00:00.000000Z"
        ),
        "part_number": 1,
        "line_number": 2 if correction else 1,
        "first_published_at": "2026-07-22T16:00:00.000000Z",
    }
    if correction:
        instance["supersedes_event_uid"] = _uid("evt", "6")
        instance["supersedes_event_digest"] = _digest("indexed-event-6")
    return _finalize(instance, "/index_entry_digest")


def publication_manifest_fixture() -> Dict[str, Any]:
    root = RUN_LOG_ROOT + "2026/07/23/"
    artifacts = [
        {
            "artifact_uid": _uid("idx", "1"),
            "artifact_operation": "PUT",
            "artifact_schema_id": INDEX_ENTRY_ID,
            "artifact_repo_path": root + "index-0001.jsonl",
            "artifact_serialization": JSONL_SERIALIZATION,
            "artifact_digest": _digest("index-put"),
            "artifact_bytes": 1024,
            "artifact_record_count": 2,
        },
        {
            "artifact_uid": _uid("drm", "2"),
            "artifact_operation": "PUT",
            "artifact_schema_id": DAILY_MANIFEST_ID,
            "artifact_repo_path": root + "manifest-0002.json",
            "artifact_serialization": OBJECT_SERIALIZATION,
            "artifact_digest": _digest("manifest-put"),
            "artifact_bytes": 4096,
            "artifact_record_count": 1,
        },
        {
            "artifact_uid": _uid("evt", "3"),
            "artifact_operation": "PUT",
            "artifact_schema_id": PUBLIC_RUN_EVENT_ID,
            "artifact_repo_path": root + "part-0001.jsonl",
            "artifact_serialization": JSONL_SERIALIZATION,
            "artifact_digest": _digest("part-put"),
            "artifact_bytes": 2048,
            "artifact_record_count": 2,
        },
        {
            "artifact_uid": _uid("evt", "4"),
            "artifact_operation": "DELETE",
            "artifact_schema_id": PUBLIC_RUN_EVENT_ID,
            "artifact_repo_path": root + "part-0002.jsonl",
            "prior_artifact_serialization": JSONL_SERIALIZATION,
            "prior_artifact_digest": _digest("shard-2"),
            "prior_artifact_bytes": 4096,
            "prior_artifact_record_count": 3,
        },
    ]
    gates = [
        {
            "gate_code": code,
            "status": "PASS",
            "evidence_digest": _digest("gate-" + code),
        }
        for code in SHARED_GATES
    ]
    return _finalize(
        {
            "schema_version": PUBLICATION_V2_ID,
            "protocol_revision": (
                "urn:linzecolin:agentdatabase:skillops:"
                "protocol:cross-pack:v1"
            ),
            "bundle_digest": CURRENT_CANDIDATE_BUNDLE_DIGEST,
            "manifest_uid": _uid("pub", "1"),
            "auto_transaction_uid": _uid("atx", "2"),
            "trigger_kind": "MANUAL",
            "created_at": "2027-07-22T19:00:00.000000Z",
            "mechanism_srv_revision": "v0.0.0.2",
            "expected_remote_head": "sha1:" + ("1" * 40),
            "settled_lanes": ["RUN_LOG"],
            "lane_manifests": [
                {
                    "lane": "RUN_LOG",
                    "lane_transaction_uid": _uid("ltx", "3"),
                    "source_watermark_ref": "run-log-daily",
                    "artifact_count": len(artifacts),
                    "artifacts": artifacts,
                }
            ],
            "shared_gates": gates,
        },
        "/manifest_digest",
    )


def retention_receipt_fixture() -> Dict[str, Any]:
    root = RUN_LOG_ROOT + "2026/07/23/"
    affected = [
        {
            "artifact_repo_path": root + "part-0002.jsonl",
            "artifact_schema_id": PUBLIC_RUN_EVENT_ID,
            "artifact_serialization": JSONL_SERIALIZATION,
            "prior_artifact_digest": _digest("shard-2"),
            "prior_artifact_bytes": 4096,
            "prior_record_count": 3,
            "first_published_at": "2026-07-22T17:00:00.000000Z",
            "retention_not_before": "2027-07-22T17:00:00.000000Z",
            "prune_deadline_at": "2027-07-23T17:00:00.000000Z",
            "retained_index_path": root + "index-0002.jsonl",
            "retained_index_digest": _digest("index-2"),
            "prior_daily_manifest_digest": _digest("daily-before-prune"),
        }
    ]
    return _finalize(
        {
            "schema_version": RETENTION_V3_ID,
            "protocol_revision": (
                "urn:linzecolin:agentdatabase:skillops:"
                "protocol:cross-pack:v1"
            ),
            "bundle_digest": CURRENT_CANDIDATE_BUNDLE_DIGEST,
            "receipt_uid": _uid("rtr", "5"),
            "retention_action_uid": _uid("rta", "6"),
            "auto_transaction_uid": _uid("atx", "7"),
            "executed_at": "2027-07-22T18:00:00.000000Z",
            "cutoff_at": "2027-07-22T17:30:00.000000Z",
            "clock_basis": "UTC_WALL_CLOCK",
            "scope": "GIT_CURRENT_TREE",
            "action": "PRUNE_CURRENT_TREE",
            "retention_policy_id": RETENTION_POLICY_V3_ID,
            "policy_snapshot_digest": _digest("retention-policy-v3"),
            "selected_count": 1,
            "selected_bytes": 4096,
            "affected_count": 1,
            "affected_bytes": 4096,
            "affected_public_artifacts": affected,
            "prune_deadline_breached": False,
            "protected_candidate_count": 0,
            "legacy_candidate_count": 0,
            "reprojection_status": "NOT_APPLICABLE",
            "offline_duration_seconds": 0,
            "ttl_breach": False,
            "history_rewrite_performed": False,
            "hard_delete_claimed": False,
            "evidence_digest": _digest("retention-evidence"),
        },
        "/receipt_digest",
    )


def legal_fixtures() -> Dict[str, Mapping[str, Any]]:
    return {
        DAILY_MANIFEST_ID: daily_manifest_fixture(),
        INDEX_ENTRY_ID: index_entry_fixture(),
        PUBLICATION_V2_ID: publication_manifest_fixture(),
        RETENTION_V3_ID: retention_receipt_fixture(),
    }


def lint_draft() -> None:
    contract = load_transport_draft()
    fixtures = legal_fixtures()
    discovered = discover_required_allowlist_additions(
        list(fixtures.values()),
        contract.bundle.policies,
    )
    expected = contract.interface[
        "required_mechanism_public_value_allowlist_additions"
    ]
    if discovered != expected:
        _fail(
            "AUTO_TRANSPORT_ALLOWLIST_DELTA_MISMATCH:"
            + ",".join(discovered)
        )
    for schema_id, fixture in fixtures.items():
        validate_transport_instance(
            contract,
            fixture,
            schema_id,
            expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
            allow_draft_policy_delta=True,
        )
    manifest = fixtures[DAILY_MANIFEST_ID]
    root = RUN_LOG_ROOT + "2026/07/23/"
    validate_manifest_tree(
        manifest,
        root + "manifest-0002.json",
        {
            root + "part-0001.jsonl": {
                "digest": manifest["parts"][0]["shard_digest"],
                "bytes": manifest["parts"][0]["shard_bytes"],
                "records": manifest["parts"][0]["record_count"],
            },
            root + "index-0001.jsonl": {
                "digest": manifest["parts"][0]["index_digest"],
                "bytes": manifest["parts"][0]["index_bytes"],
                "records": manifest["parts"][0]["index_record_count"],
            },
            root + "index-0002.jsonl": {
                "digest": manifest["parts"][1]["index_digest"],
                "bytes": manifest["parts"][1]["index_bytes"],
                "records": manifest["parts"][1]["index_record_count"],
            },
        },
    )
    retention_receipt = fixtures[RETENTION_V3_ID]
    validate_pruned_manifest_receipt_links(
        manifest,
        root + "manifest-0002.json",
        {
            manifest["parts"][1][
                "retention_receipt_path"
            ]: retention_receipt,
        },
    )
    rows = [index_entry_fixture(), index_entry_fixture(correction=True)]
    validate_index_entries(
        rows,
        event_rows=rows,
        expected_part_number=1,
        expected_record_count=2,
    )
    print(
        "AUTO_TRANSPORT_DRAFT_VALID "
        "current=29/5 target=31/5 "
        f"allowlist_delta={','.join(discovered)}"
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("lint-draft")
    validate = commands.add_parser("validate-object")
    validate.add_argument("--instance", type=Path, required=True)
    validate.add_argument("--schema-id", required=True)
    validate.add_argument(
        "--expected-bundle-digest",
        default=CURRENT_CANDIDATE_BUNDLE_DIGEST,
    )
    validate.add_argument("--allow-draft-policy-delta", action="store_true")
    jsonl = commands.add_parser("validate-jsonl")
    jsonl.add_argument("--instance", type=Path, required=True)
    jsonl.add_argument("--schema-id", required=True)
    jsonl.add_argument(
        "--expected-bundle-digest",
        default=CURRENT_CANDIDATE_BUNDLE_DIGEST,
    )
    jsonl.add_argument("--allow-draft-policy-delta", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "lint-draft":
            lint_draft()
            return 0
        contract = load_transport_draft()
        raw = args.instance.read_bytes()
        if args.command == "validate-object":
            validate_jcs_object_bytes(
                raw,
                contract,
                args.schema_id,
                expected_bundle_digest=args.expected_bundle_digest,
                allow_draft_policy_delta=args.allow_draft_policy_delta,
            )
        else:
            validate_jcs_jsonl_bytes(
                raw,
                contract,
                args.schema_id,
                expected_bundle_digest=args.expected_bundle_digest,
                allow_draft_policy_delta=args.allow_draft_policy_delta,
            )
    except (ContractError, OSError, ValueError) as exc:
        print(f"AUTO_TRANSPORT_DRAFT_INVALID:{exc}", file=sys.stderr)
        return 2
    print("AUTO_TRANSPORT_DRAFT_INSTANCE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
