#!/usr/bin/env python3
"""Validate Mechanism-owned AU-040 policy and cross-artifact semantics."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import re
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping, Optional, Sequence
from zoneinfo import ZoneInfo


GOVERNANCE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GOVERNANCE_DIR.parents[1]
sys.path.insert(0, str(GOVERNANCE_DIR / "tools"))
sys.path.insert(0, str(REPO_ROOT))

from build_au040_semantic_acceptance import (  # noqa: E402
    AUTO_DRAFT_INTERFACE_RAW_SHA256,
    AUTO_SCHEMA_CONTRACTS,
    CURRENT_CANDIDATE_BUNDLE_DIGEST,
    OUTPUT_INTERFACE,
    POLICY_V2_DIR,
    PROTOCOL,
    PUBLIC_VALUE_ALLOWLIST_ADDITIONS,
    PUBLIC_VALUE_POLICY_V1,
    PUBLIC_VALUE_POLICY_V2,
    PUBLIC_VALUE_SCHEMA_V1,
    PUBLIC_VALUE_SCHEMA_V2,
    RETENTION_POLICY_V2,
    RETENTION_POLICY_V3,
    RETENTION_SCHEMA_V2,
    RETENTION_SCHEMA_V3,
    SCHEMA_V2_DIR,
    materialize,
    semantic_policy_acceptance,
)
from canonical_json import (  # noqa: E402
    CanonicalizationError,
    canonicalize_object,
    parse_json_bytes,
)
from validate_mechanism import (  # noqa: E402
    ContractBundle,
    ContractError,
    build_registry,
    scan_public_value,
    strict_load,
    validate_instance,
)
from validate_public_run_event import (  # noqa: E402
    PUBLIC_RUN_EVENT_SCHEMA_ID,
    validate_public_run_event,
)
from CodexSkills.registry.auto.tools.validate_transport_draft import (  # noqa: E402
    DAILY_MANIFEST_ID,
    INDEX_ENTRY_ID,
    JSONL_SERIALIZATION,
    OBJECT_SERIALIZATION,
    PUBLICATION_V2_ID,
    RETENTION_V3_ID,
    TransportDraftContract,
    _validate_index_entry,
    load_transport_draft,
    validate_index_entries,
    validate_pruned_manifest_receipt_links,
    validate_transport_instance,
)


MAX_PART_BYTES = 20 * 1024 * 1024
RETENTION_ELAPSED = dt.timedelta(days=365)
PRUNE_DEADLINE = dt.timedelta(hours=24)
SYDNEY = ZoneInfo("Australia/Sydney")
RUN_LOG_ROOT = "OpenAIDatabase/data/run_logs/skills_runs/"
DAILY_PATH_RE = re.compile(
    r"^OpenAIDatabase/data/run_logs/skills_runs/"
    r"(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/"
    r"(?P<kind>manifest|index|part)-(?P<number>[0-9]{4})"
    r"\.(?P<extension>json|jsonl)$"
)
RETENTION_RECEIPT_PATH_RE = re.compile(
    r"^OpenAIDatabase/data/run_logs/skills_runs/"
    r"(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/"
    r"retention-receipt-(?P<number>[0-9]{4})\.json$"
)
IMMUTABLE_PART_FIELDS = (
    "part_number",
    "shard_name",
    "shard_digest",
    "shard_bytes",
    "record_count",
    "index_name",
    "index_digest",
    "index_bytes",
    "index_record_count",
    "first_event_uid",
    "first_event_digest",
    "first_occurred_at",
    "last_event_uid",
    "last_event_digest",
    "last_occurred_at",
    "first_published_at",
    "retention_not_before",
)


@dataclasses.dataclass(frozen=True)
class AU040AcceptanceContract:
    bundle: ContractBundle
    transport: TransportDraftContract
    interface: Mapping[str, Any]
    public_value_policy: Mapping[str, Any]
    retention_policy: Mapping[str, Any]


def _fail(code: str) -> None:
    raise ContractError(code)


def _parse_utc(value: str) -> dt.datetime:
    try:
        return dt.datetime.strptime(
            value,
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ).replace(tzinfo=dt.timezone.utc)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"AU040_UTC_TIMESTAMP_INVALID:{value}") from exc


def _calendar_date(path_match: re.Match[str]) -> str:
    try:
        value = dt.date(
            int(path_match.group("year")),
            int(path_match.group("month")),
            int(path_match.group("day")),
        )
    except ValueError as exc:
        raise ContractError("AU040_REPO_PATH_DATE_INVALID") from exc
    return value.isoformat()


def _load_policy(path: Path) -> Mapping[str, Any]:
    value = strict_load(path)
    if not isinstance(value, dict):
        _fail(f"AU040_POLICY_ROOT_INVALID:{path}")
    return value


def _scanner_policies(
    policies: Mapping[str, Any],
    public_value_policy: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Alias v2 under the legacy scanner key without trusting v1 semantics."""

    result = dict(policies)
    result[PUBLIC_VALUE_POLICY_V1] = public_value_policy
    result[PUBLIC_VALUE_POLICY_V2] = public_value_policy
    return result


def load_au040_acceptance() -> AU040AcceptanceContract:
    materialize(check=True)
    expected_interface = semantic_policy_acceptance()
    interface = strict_load(OUTPUT_INTERFACE)
    if interface != expected_interface:
        _fail("AU040_ACCEPTANCE_INTERFACE_SEMANTIC_DRIFT")
    if (
        interface.get("status")
        != "DRAFT_NON_ACTIVE_SEMANTIC_POLICY_ACCEPTED"
        or interface.get("owner_plane") != "MECHANISM"
        or interface.get("repository_bound") is not False
        or interface.get("bundle_materialization_forbidden") is not True
        or interface.get("activation_forbidden") is not True
        or interface.get("canonical_publication_permitted") is not False
        or interface.get("protocol_revision") != PROTOCOL
        or interface.get("next_phase")
        != "AUTO_SCHEMA_PROMOTION_TO_FINAL_PATHS"
    ):
        _fail("AU040_ACCEPTANCE_STATE_INVALID")
    source = interface.get("source_auto_draft_trust", {})
    if (
        source.get("expected_interface_object_id")
        != "sha256:" + AUTO_DRAFT_INTERFACE_RAW_SHA256
        or source.get("mode") != "DRAFT_NON_ACTIVE"
    ):
        _fail("AU040_AUTO_DRAFT_TRUST_TUPLE_INVALID")

    transport = load_transport_draft()
    target_schemas: Dict[str, Any] = dict(transport.bundle.schemas)
    target_pointers: Dict[str, Optional[str]] = dict(
        transport.bundle.self_digest_pointers
    )
    for old_id in (PUBLIC_VALUE_SCHEMA_V1, RETENTION_SCHEMA_V2):
        if old_id not in target_schemas:
            _fail(f"AU040_REPLACED_POLICY_SCHEMA_MISSING:{old_id}")
        target_schemas.pop(old_id)
        target_pointers.pop(old_id, None)
    policy_schemas = {
        PUBLIC_VALUE_SCHEMA_V2: strict_load(
            SCHEMA_V2_DIR / "public-value-policy.schema.json"
        ),
        RETENTION_SCHEMA_V3: strict_load(
            SCHEMA_V2_DIR / "retention-policy.schema.json"
        ),
    }
    target_schemas.update(policy_schemas)
    target_pointers.update(
        {
            PUBLIC_VALUE_SCHEMA_V2: None,
            RETENTION_SCHEMA_V3: None,
        }
    )
    if len(target_schemas) != 31:
        _fail("AU040_TARGET_SCHEMA_COUNT_NOT_31")

    public_value_policy = _load_policy(
        POLICY_V2_DIR / "public-value-policy.v2.json"
    )
    retention_policy = _load_policy(
        POLICY_V2_DIR / "retention-policy.v3.json"
    )
    target_policies = dict(transport.bundle.policies)
    for old_id in (PUBLIC_VALUE_POLICY_V1, RETENTION_POLICY_V2):
        if old_id not in target_policies:
            _fail(f"AU040_REPLACED_POLICY_MISSING:{old_id}")
        target_policies.pop(old_id)
    target_policies[PUBLIC_VALUE_POLICY_V2] = public_value_policy
    target_policies[RETENTION_POLICY_V3] = retention_policy
    if len(target_policies) != 5:
        _fail("AU040_TARGET_POLICY_COUNT_NOT_5")

    registry, format_checker = build_registry(target_schemas)
    bundle = ContractBundle(
        target_schemas,
        registry,
        format_checker,
        target_pointers,
        target_policies,
        PROTOCOL,
    )
    validate_instance(
        bundle,
        public_value_policy,
        PUBLIC_VALUE_SCHEMA_V2,
        verify_digest=False,
    )
    validate_instance(
        bundle,
        retention_policy,
        RETENTION_SCHEMA_V3,
        verify_digest=False,
    )
    _validate_policy_semantics(
        transport,
        public_value_policy,
        retention_policy,
    )
    return AU040AcceptanceContract(
        bundle,
        transport,
        interface,
        public_value_policy,
        retention_policy,
    )


def _validate_policy_semantics(
    transport: TransportDraftContract,
    public_value_policy: Mapping[str, Any],
    retention_policy: Mapping[str, Any],
) -> None:
    current_public = transport.current_candidate.policies[
        PUBLIC_VALUE_POLICY_V1
    ]
    old_allowed = set(current_public["allowed_high_entropy_field_names"])
    new_allowed = set(
        public_value_policy["allowed_high_entropy_field_names"]
    )
    if new_allowed.difference(old_allowed) != set(
        PUBLIC_VALUE_ALLOWLIST_ADDITIONS
    ):
        _fail("AU040_PUBLIC_VALUE_ALLOWLIST_DELTA_NOT_EXACT")
    if (
        public_value_policy["allowed_high_entropy_field_names"]
        != sorted(new_allowed)
        or public_value_policy["detectors"] != current_public["detectors"]
        or public_value_policy["forbidden_field_names"]
        != current_public["forbidden_field_names"]
        or public_value_policy["recipient_rule"]
        != current_public["recipient_rule"]
    ):
        _fail("AU040_PUBLIC_VALUE_BASELINE_DRIFT")
    if (
        retention_policy.get("sanitized_public_elapsed_seconds")
        != int(RETENTION_ELAPSED.total_seconds())
        or retention_policy.get("prune_deadline_hours_after_eligibility")
        != 24
        or retention_policy.get("retention_clock_schedule_independent")
        is not True
        or retention_policy.get("boundary_at_retention_not_before_retained")
        is not True
        or retention_policy.get("prune_deadline_equal_is_on_time")
        is not True
        or retention_policy.get("prune_deadline_hard_guarantee_claimed")
        is not False
        or retention_policy.get("history_rewrite_allowed") is not False
    ):
        _fail("AU040_RETENTION_POLICY_SEMANTICS_INVALID")


def validate_public_value_v2(
    contract: AU040AcceptanceContract,
    value: Any,
) -> None:
    scan_public_value(
        value,
        _scanner_policies(
            contract.bundle.policies,
            contract.public_value_policy,
        ),
    )


def _public_scanner_bundle(
    contract: AU040AcceptanceContract,
) -> ContractBundle:
    return ContractBundle(
        contract.bundle.schemas,
        contract.bundle.registry,
        contract.bundle.format_checker,
        contract.bundle.self_digest_pointers,
        _scanner_policies(
            contract.bundle.policies,
            contract.public_value_policy,
        ),
        contract.bundle.protocol_revision,
    )


def validate_retention_anchor(
    first_published_at: str,
    retention_not_before: str,
) -> None:
    first = _parse_utc(first_published_at)
    anchor = _parse_utc(retention_not_before)
    if anchor != first + RETENTION_ELAPSED:
        _fail("AU040_RETENTION_ANCHOR_NOT_EXACT_365D")


def current_tree_prune_eligible(
    now: str,
    retention_not_before: str,
) -> bool:
    return _parse_utc(now) > _parse_utc(retention_not_before)


def prune_deadline_breached(
    executed_at: str,
    retention_not_before: str,
) -> bool:
    return (
        _parse_utc(executed_at)
        > _parse_utc(retention_not_before) + PRUNE_DEADLINE
    )


def validate_daily_manifest_semantics(
    contract: AU040AcceptanceContract,
    instance: Mapping[str, Any],
) -> None:
    validate_transport_instance(
        contract.transport,
        instance,
        DAILY_MANIFEST_ID,
        expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
        allow_draft_policy_delta=True,
    )
    validate_public_value_v2(contract, instance)
    for part in instance["parts"]:
        validate_retention_anchor(
            part["first_published_at"],
            part["retention_not_before"],
        )


def validate_retention_receipt_semantics(
    contract: AU040AcceptanceContract,
    instance: Mapping[str, Any],
) -> None:
    validate_transport_instance(
        contract.transport,
        instance,
        RETENTION_V3_ID,
        expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
        allow_draft_policy_delta=True,
    )
    validate_public_value_v2(contract, instance)
    if (
        instance["scope"] == "GIT_CURRENT_TREE"
        and instance["action"] == "PRUNE_CURRENT_TREE"
    ):
        observed_breach = False
        for item in instance["affected_public_artifacts"]:
            validate_retention_anchor(
                item["first_published_at"],
                item["retention_not_before"],
            )
            if (
                _parse_utc(item["prune_deadline_at"])
                != _parse_utc(item["retention_not_before"])
                + PRUNE_DEADLINE
            ):
                _fail("AU040_PRUNE_DEADLINE_NOT_EXACT_24H")
            observed_breach = (
                observed_breach
                or prune_deadline_breached(
                    instance["executed_at"],
                    item["retention_not_before"],
                )
            )
        if instance["prune_deadline_breached"] is not observed_breach:
            _fail("AU040_PRUNE_DEADLINE_BREACH_STATE_MISMATCH")


def _manifest_path(
    path: str,
    expected_revision: int,
) -> tuple[str, int]:
    match = DAILY_PATH_RE.fullmatch(path)
    if (
        match is None
        or match.group("kind") != "manifest"
        or match.group("extension") != "json"
    ):
        _fail("AU040_MANIFEST_CHAIN_PATH_INVALID")
    date = _calendar_date(match)
    number = int(match.group("number"))
    if number != expected_revision:
        _fail("AU040_MANIFEST_CHAIN_PATH_REVISION_MISMATCH")
    return date, number


def validate_manifest_revision_chain(
    contract: AU040AcceptanceContract,
    current: Mapping[str, Any],
    current_repo_path: str,
    prior: Optional[Mapping[str, Any]],
    prior_repo_path: Optional[str],
) -> None:
    validate_daily_manifest_semantics(contract, current)
    current_revision = current["manifest_revision"]
    current_date, _ = _manifest_path(current_repo_path, current_revision)
    if current_date != current["local_date"]:
        _fail("AU040_MANIFEST_CHAIN_CURRENT_DATE_MISMATCH")
    if current_revision == 1:
        if prior is not None or prior_repo_path is not None:
            _fail("AU040_MANIFEST_REVISION_ONE_PRIOR_FORBIDDEN")
        if current["previous_manifest_digest"] is not None:
            _fail("AU040_MANIFEST_REVISION_ONE_DIGEST_FORBIDDEN")
        if any(part["state"] != "ACTIVE" for part in current["parts"]):
            _fail("AU040_MANIFEST_NEW_PART_MUST_START_ACTIVE")
        return
    if prior is None or prior_repo_path is None:
        _fail("AU040_MANIFEST_PREDECESSOR_REQUIRED")
    validate_daily_manifest_semantics(contract, prior)
    prior_revision = prior["manifest_revision"]
    prior_date, _ = _manifest_path(prior_repo_path, prior_revision)
    if (
        prior_revision != current_revision - 1
        or prior_date != current_date
        or prior["local_date"] != current["local_date"]
    ):
        _fail("AU040_MANIFEST_PREDECESSOR_SEQUENCE_INVALID")
    if current["previous_manifest_digest"] != prior["manifest_digest"]:
        _fail("AU040_MANIFEST_PREDECESSOR_DIGEST_MISMATCH")
    if (
        _parse_utc(current["publication_transaction_at"])
        < _parse_utc(prior["publication_transaction_at"])
    ):
        _fail("AU040_MANIFEST_PUBLICATION_TIME_REVERSED")
    prior_parts = prior["parts"]
    current_parts = current["parts"]
    if len(current_parts) < len(prior_parts):
        _fail("AU040_MANIFEST_PART_REMOVAL_FORBIDDEN")
    for old, new in zip(prior_parts, current_parts):
        if any(old.get(field) != new.get(field) for field in IMMUTABLE_PART_FIELDS):
            _fail("AU040_MANIFEST_EXISTING_PART_MUTATED")
        if old["state"] == "PRUNED" and new != old:
            _fail("AU040_MANIFEST_PRUNED_PART_MUTATED")
        if old["state"] == "ACTIVE" and new["state"] not in {
            "ACTIVE",
            "PRUNED",
        }:
            _fail("AU040_MANIFEST_PART_STATE_TRANSITION_INVALID")
        if old["state"] == "ACTIVE" and new["state"] == "ACTIVE" and new != old:
            _fail("AU040_MANIFEST_ACTIVE_PART_MUTATED")
    if any(
        part["state"] != "ACTIVE"
        for part in current_parts[len(prior_parts) :]
    ):
        _fail("AU040_MANIFEST_NEW_PART_MUST_START_ACTIVE")


def _parse_canonical_jsonl(raw: bytes, *, max_bytes: int) -> list[Any]:
    if (
        not raw
        or len(raw) > max_bytes
        or not raw.endswith(b"\n")
        or raw.startswith(b"\xef\xbb\xbf")
        or b"\r" in raw
    ):
        _fail("AU040_JSONL_FRAMING_INVALID")
    rows = []
    for line_number, line in enumerate(raw[:-1].split(b"\n"), 1):
        if not line:
            _fail(f"AU040_JSONL_EMPTY_LINE:{line_number}")
        try:
            value = parse_json_bytes(line)
        except CanonicalizationError as exc:
            raise ContractError(
                f"AU040_JSONL_STRICT_JSON_REJECTED:{line_number}:{exc}"
            ) from exc
        if canonicalize_object(value) != line:
            _fail(f"AU040_JSONL_LINE_NOT_RFC8785_JCS:{line_number}")
        rows.append(value)
    return rows


def validate_part_index_manifest_closure(
    contract: AU040AcceptanceContract,
    manifest: Mapping[str, Any],
    *,
    part_number: int,
    part_bytes: bytes,
    index_bytes: bytes,
    known_events: Optional[Mapping[str, str]] = None,
) -> None:
    validate_daily_manifest_semantics(contract, manifest)
    matching = [
        part
        for part in manifest["parts"]
        if part["part_number"] == part_number
    ]
    if len(matching) != 1:
        _fail("AU040_MANIFEST_PART_NUMBER_NOT_EXACT")
    part = matching[0]
    if part["state"] != "ACTIVE":
        _fail("AU040_CLOSURE_REQUIRES_ACTIVE_PART")
    event_rows = _parse_canonical_jsonl(
        part_bytes,
        max_bytes=MAX_PART_BYTES,
    )
    index_rows = _parse_canonical_jsonl(
        index_bytes,
        max_bytes=MAX_PART_BYTES,
    )
    for event in event_rows:
        validate_public_run_event(
            _public_scanner_bundle(contract),
            event,
            expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
        )
    for entry in index_rows:
        validate_instance(
            contract.bundle,
            entry,
            INDEX_ENTRY_ID,
            expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
            public=False,
        )
        _validate_index_entry(entry)
        validate_public_value_v2(contract, entry)
    validate_index_entries(
        index_rows,
        event_rows=event_rows,
        expected_part_number=part_number,
        expected_record_count=part["record_count"],
        known_events=known_events,
    )
    if any(
        entry["first_published_at"] != part["first_published_at"]
        for entry in index_rows
    ):
        _fail("AU040_INDEX_FIRST_PUBLISHED_AT_PART_MISMATCH")
    first_event = event_rows[0]
    last_event = event_rows[-1]
    expected_boundary = {
        "first_event_uid": first_event["event_uid"],
        "first_event_digest": first_event["event_digest"],
        "first_occurred_at": first_event["occurred_at"],
        "last_event_uid": last_event["event_uid"],
        "last_event_digest": last_event["event_digest"],
        "last_occurred_at": last_event["occurred_at"],
    }
    if any(part[key] != value for key, value in expected_boundary.items()):
        _fail("AU040_MANIFEST_EVENT_BOUNDARY_MISMATCH")
    if any(
        _parse_utc(event["occurred_at"]).astimezone(SYDNEY).date().isoformat()
        != manifest["local_date"]
        for event in event_rows
    ):
        _fail("AU040_EVENT_SYDNEY_DATE_MISMATCH")
    expected_physical = {
        "shard_digest": hashlib.sha256(part_bytes).hexdigest(),
        "shard_bytes": len(part_bytes),
        "record_count": len(event_rows),
        "index_digest": hashlib.sha256(index_bytes).hexdigest(),
        "index_bytes": len(index_bytes),
        "index_record_count": len(index_rows),
    }
    if any(part[key] != value for key, value in expected_physical.items()):
        _fail("AU040_MANIFEST_PHYSICAL_ARTIFACT_MISMATCH")


def _daily_artifact_path(path: str) -> tuple[str, str, int]:
    match = DAILY_PATH_RE.fullmatch(path)
    if match is not None:
        date = _calendar_date(match)
        kind = match.group("kind")
        number = int(match.group("number"))
        extension = match.group("extension")
        if number < 1 or number > 9999:
            _fail("AU040_RUN_LOG_ARTIFACT_SEQUENCE_INVALID")
        if (
            (kind == "manifest" and extension != "json")
            or (kind != "manifest" and extension != "jsonl")
        ):
            _fail("AU040_RUN_LOG_ARTIFACT_EXTENSION_INVALID")
        return date, kind, number
    receipt = RETENTION_RECEIPT_PATH_RE.fullmatch(path)
    if receipt is None:
        _fail(f"AU040_RUN_LOG_ARTIFACT_PATH_INVALID:{path}")
    date = _calendar_date(receipt)
    number = int(receipt.group("number"))
    if number < 1 or number > 9999:
        _fail("AU040_RETENTION_RECEIPT_SEQUENCE_INVALID")
    return date, "retention-receipt", number


def validate_publication_artifact_set(
    contract: AU040AcceptanceContract,
    instance: Mapping[str, Any],
) -> None:
    validate_instance(
        contract.bundle,
        instance,
        PUBLICATION_V2_ID,
        expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
        public=False,
    )
    validate_public_value_v2(contract, instance)
    lane_names = [lane["lane"] for lane in instance["lane_manifests"]]
    if lane_names != sorted(lane_names) or lane_names != instance["settled_lanes"]:
        _fail("AU040_PUBLICATION_LANE_ORDER_OR_SETTLEMENT_MISMATCH")
    seen_paths = set()
    seen_uids = set()
    for lane in instance["lane_manifests"]:
        artifacts = lane["artifacts"]
        if lane["artifact_count"] != len(artifacts):
            _fail("AU040_PUBLICATION_ARTIFACT_COUNT_MISMATCH")
        keys = [
            (item["artifact_repo_path"], item["artifact_uid"])
            for item in artifacts
        ]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            _fail("AU040_PUBLICATION_ARTIFACT_ORDER_INVALID")
        for artifact in artifacts:
            path = artifact["artifact_repo_path"]
            uid = artifact["artifact_uid"]
            if path in seen_paths or uid in seen_uids:
                _fail("AU040_PUBLICATION_ARTIFACT_DUPLICATE")
            seen_paths.add(path)
            seen_uids.add(uid)
        if lane["lane"] != "RUN_LOG":
            continue
        by_date: MutableMapping[str, list[tuple[str, int, Mapping[str, Any]]]]
        by_date = {}
        for artifact in artifacts:
            date, kind, number = _daily_artifact_path(
                artifact["artifact_repo_path"]
            )
            by_date.setdefault(date, []).append((kind, number, artifact))
            operation = artifact["artifact_operation"]
            schema_id = artifact["artifact_schema_id"]
            serialization = artifact[
                "artifact_serialization"
                if operation == "PUT"
                else "prior_artifact_serialization"
            ]
            if kind == "part":
                if (
                    schema_id != PUBLIC_RUN_EVENT_SCHEMA_ID
                    or serialization != JSONL_SERIALIZATION
                ):
                    _fail("AU040_PUBLICATION_PART_CONTRACT_MISMATCH")
            elif kind == "index":
                if (
                    operation != "PUT"
                    or schema_id != INDEX_ENTRY_ID
                    or serialization != JSONL_SERIALIZATION
                ):
                    _fail("AU040_PUBLICATION_INDEX_CONTRACT_MISMATCH")
            elif kind == "manifest":
                if (
                    operation != "PUT"
                    or schema_id != DAILY_MANIFEST_ID
                    or serialization != OBJECT_SERIALIZATION
                ):
                    _fail("AU040_PUBLICATION_DAILY_MANIFEST_CONTRACT_MISMATCH")
            elif (
                operation != "PUT"
                or schema_id != RETENTION_V3_ID
                or serialization != OBJECT_SERIALIZATION
            ):
                _fail("AU040_PUBLICATION_RETENTION_RECEIPT_CONTRACT_MISMATCH")
        for date, dated in by_date.items():
            manifests = [
                item
                for kind, _, item in dated
                if kind == "manifest"
            ]
            if len(manifests) != 1:
                _fail(
                    "AU040_PUBLICATION_EXACTLY_ONE_DAILY_MANIFEST_REQUIRED:"
                    + date
                )
            index_puts = {
                number
                for kind, number, item in dated
                if kind == "index" and item["artifact_operation"] == "PUT"
            }
            part_puts = {
                number
                for kind, number, item in dated
                if kind == "part" and item["artifact_operation"] == "PUT"
            }
            part_deletes = {
                number
                for kind, number, item in dated
                if kind == "part" and item["artifact_operation"] == "DELETE"
            }
            receipts = [
                item
                for kind, _, item in dated
                if kind == "retention-receipt"
            ]
            if index_puts != part_puts:
                _fail("AU040_PUBLICATION_PART_INDEX_PUT_SET_MISMATCH")
            if part_deletes and not receipts:
                _fail("AU040_PUBLICATION_PRUNE_RECEIPT_PUT_REQUIRED")
            if receipts and not part_deletes:
                _fail("AU040_PUBLICATION_ORPHAN_RETENTION_RECEIPT")


def _run_log_descriptor_map(
    publication: Mapping[str, Any],
) -> Mapping[str, Mapping[str, Any]]:
    descriptors: Dict[str, Mapping[str, Any]] = {}
    for lane in publication["lane_manifests"]:
        if lane["lane"] != "RUN_LOG":
            continue
        for artifact in lane["artifacts"]:
            descriptors[artifact["artifact_repo_path"]] = artifact
    return descriptors


def _validate_put_descriptor_bytes(
    descriptor: Mapping[str, Any],
    raw: bytes,
    *,
    expected_schema_id: str,
    expected_serialization: str,
    expected_record_count: int,
) -> None:
    if (
        descriptor.get("artifact_operation") != "PUT"
        or descriptor.get("artifact_schema_id") != expected_schema_id
        or descriptor.get("artifact_serialization")
        != expected_serialization
        or descriptor.get("artifact_digest")
        != hashlib.sha256(raw).hexdigest()
        or descriptor.get("artifact_bytes") != len(raw)
        or descriptor.get("artifact_record_count")
        != expected_record_count
    ):
        _fail("AU040_PUBLICATION_PUT_DESCRIPTOR_BYTES_MISMATCH")


def validate_shard_transaction_closure(
    contract: AU040AcceptanceContract,
    publication: Mapping[str, Any],
    manifest: Mapping[str, Any],
    manifest_repo_path: str,
    *,
    part_number: int,
    part_bytes: bytes,
    index_bytes: bytes,
) -> None:
    """Close one new immutable part against its transaction descriptors."""

    validate_publication_artifact_set(contract, publication)
    validate_part_index_manifest_closure(
        contract,
        manifest,
        part_number=part_number,
        part_bytes=part_bytes,
        index_bytes=index_bytes,
    )
    if (
        publication["auto_transaction_uid"]
        != manifest["auto_transaction_uid"]
        or publication["created_at"]
        != manifest["publication_transaction_at"]
    ):
        _fail("AU040_PUBLICATION_MANIFEST_TRANSACTION_MISMATCH")
    prefix = manifest_repo_path.rsplit("/", 1)[0] + "/"
    descriptors = _run_log_descriptor_map(publication)
    part_path = prefix + f"part-{part_number:04d}.jsonl"
    index_path = prefix + f"index-{part_number:04d}.jsonl"
    required = (manifest_repo_path, part_path, index_path)
    if any(path not in descriptors for path in required):
        _fail("AU040_SHARD_TRANSACTION_DESCRIPTOR_MISSING")
    manifest_raw = canonicalize_object(manifest)
    _validate_put_descriptor_bytes(
        descriptors[manifest_repo_path],
        manifest_raw,
        expected_schema_id=DAILY_MANIFEST_ID,
        expected_serialization=OBJECT_SERIALIZATION,
        expected_record_count=1,
    )
    _validate_put_descriptor_bytes(
        descriptors[part_path],
        part_bytes,
        expected_schema_id=PUBLIC_RUN_EVENT_SCHEMA_ID,
        expected_serialization=JSONL_SERIALIZATION,
        expected_record_count=manifest["parts"][part_number - 1][
            "record_count"
        ],
    )
    _validate_put_descriptor_bytes(
        descriptors[index_path],
        index_bytes,
        expected_schema_id=INDEX_ENTRY_ID,
        expected_serialization=JSONL_SERIALIZATION,
        expected_record_count=manifest["parts"][part_number - 1][
            "index_record_count"
        ],
    )


def validate_prune_transaction_closure(
    contract: AU040AcceptanceContract,
    publication: Mapping[str, Any],
    manifest: Mapping[str, Any],
    manifest_repo_path: str,
    receipt_objects: Mapping[str, Mapping[str, Any]],
) -> None:
    """Bind deleted parts, published receipts, and the new daily manifest."""

    validate_publication_artifact_set(contract, publication)
    validate_daily_manifest_semantics(contract, manifest)
    if (
        publication["auto_transaction_uid"]
        != manifest["auto_transaction_uid"]
        or publication["created_at"]
        != manifest["publication_transaction_at"]
    ):
        _fail("AU040_PUBLICATION_MANIFEST_TRANSACTION_MISMATCH")
    descriptors = _run_log_descriptor_map(publication)
    manifest_descriptor = descriptors.get(manifest_repo_path)
    if manifest_descriptor is None:
        _fail("AU040_PRUNE_TRANSACTION_MANIFEST_DESCRIPTOR_MISSING")
    _validate_put_descriptor_bytes(
        manifest_descriptor,
        canonicalize_object(manifest),
        expected_schema_id=DAILY_MANIFEST_ID,
        expected_serialization=OBJECT_SERIALIZATION,
        expected_record_count=1,
    )
    published_receipt_paths = {
        path
        for path, descriptor in descriptors.items()
        if descriptor["artifact_schema_id"] == RETENTION_V3_ID
    }
    deleted_part_descriptors = {
        path: descriptor
        for path, descriptor in descriptors.items()
        if (
            descriptor["artifact_schema_id"] == PUBLIC_RUN_EVENT_SCHEMA_ID
            and descriptor["artifact_operation"] == "DELETE"
        )
    }
    if not published_receipt_paths or not deleted_part_descriptors:
        _fail("AU040_PRUNE_TRANSACTION_ARTIFACT_SET_INCOMPLETE")
    for path in published_receipt_paths:
        receipt = receipt_objects.get(path)
        if receipt is None:
            _fail("AU040_PRUNE_TRANSACTION_RECEIPT_OBJECT_MISSING")
        validate_retention_receipt_semantics(contract, receipt)
        if receipt["auto_transaction_uid"] != publication[
            "auto_transaction_uid"
        ]:
            _fail("AU040_RETENTION_RECEIPT_TRANSACTION_MISMATCH")
        _validate_put_descriptor_bytes(
            descriptors[path],
            canonicalize_object(receipt),
            expected_schema_id=RETENTION_V3_ID,
            expected_serialization=OBJECT_SERIALIZATION,
            expected_record_count=1,
        )
    affected: Dict[str, Mapping[str, Any]] = {}
    for path in published_receipt_paths:
        for item in receipt_objects[path]["affected_public_artifacts"]:
            artifact_path = item["artifact_repo_path"]
            if artifact_path in affected:
                _fail("AU040_RETENTION_AFFECTED_PART_DUPLICATE")
            affected[artifact_path] = item
    if set(affected) != set(deleted_part_descriptors):
        _fail("AU040_RETENTION_DELETE_AFFECTED_SET_MISMATCH")
    for path, descriptor in deleted_part_descriptors.items():
        item = affected[path]
        if (
            descriptor["prior_artifact_digest"]
            != item["prior_artifact_digest"]
            or descriptor["prior_artifact_bytes"]
            != item["prior_artifact_bytes"]
            or descriptor["prior_artifact_record_count"]
            != item["prior_record_count"]
        ):
            _fail("AU040_RETENTION_DELETE_DESCRIPTOR_MISMATCH")
    validate_pruned_manifest_receipt_links(
        manifest,
        manifest_repo_path,
        receipt_objects,
    )


def lint_acceptance() -> None:
    contract = load_au040_acceptance()
    interface = contract.interface
    validate_public_value_v2(contract, interface)
    validate_public_value_v2(contract, contract.public_value_policy)
    validate_public_value_v2(contract, contract.retention_policy)
    if (
        len(interface["accepted_auto_transport_schemas"]) != 4
        or {
            (
                entry["id"],
                entry["schema_sha256"],
                entry["self_digest_pointer"],
            )
            for entry in interface["accepted_auto_transport_schemas"]
        }
        != set(AUTO_SCHEMA_CONTRACTS)
    ):
        _fail("AU040_ACCEPTED_AUTO_SCHEMA_SET_MISMATCH")
    target = interface["target_shared_set"]
    if (
        target["current_schema_count"] != 29
        or target["target_schema_count"] != 31
        or target["current_policy_count"] != 5
        or target["target_policy_count"] != 5
        or set(target["replaced_policy_ids"])
        != {PUBLIC_VALUE_POLICY_V1, RETENTION_POLICY_V2}
        or set(target["replacement_policy_ids"])
        != {PUBLIC_VALUE_POLICY_V2, RETENTION_POLICY_V3}
    ):
        _fail("AU040_TARGET_SHARED_SET_INVALID")
    print(
        "MECHANISM_AU040_SEMANTIC_POLICY_ACCEPTANCE_VALID "
        "current=29/5 target=31/5 repository_bound=false active=false"
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("lint-acceptance")
    args = parser.parse_args(argv)
    if args.command == "lint-acceptance":
        lint_acceptance()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
