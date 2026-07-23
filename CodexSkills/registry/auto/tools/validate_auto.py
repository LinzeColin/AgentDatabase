#!/usr/bin/env python3
"""Fail-closed offline validator for the non-active SkillOps Auto contract.

The Mechanism draft is the authority for canonicalization, schema resolution,
formats, shared policy, and public-value scanning.  This module only composes
the Auto-owned schemas into that trusted draft and enforces Auto-owned
cross-field invariants.  It never resolves a schema over the network.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo


AUTO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTO_DIR.parents[2]
GOVERNANCE_DIR = REPO_ROOT / "CodexSkills" / "governance"
GOVERNANCE_TOOLS = GOVERNANCE_DIR / "tools"
sys.path.insert(0, str(GOVERNANCE_TOOLS))

from canonical_json import (  # noqa: E402
    CanonicalizationError,
    canonicalize_object,
    parse_json_bytes,
)
from validate_mechanism import (  # noqa: E402
    ContractBundle,
    ContractError,
    EXPECTED_SCHEMA_SELF_POINTERS,
    FINAL_AUTO_PUBLIC_SCHEMA_IDS,
    FINAL_POLICY_IDS,
    FINAL_SCHEMA_SELF_POINTERS,
    PROTOCOL,
    TrustTuple,
    build_registry,
    capability_gate,
    load_draft_contract,
    load_schema_directories,
    load_trusted_bundle,
    scan_public_value,
    strict_load,
    validate_instance,
)


SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
PUBLIC_SELF_POINTERS = {
    SCHEMA_PREFIX + "auto-receipt:v2": "/receipt_digest",
    SCHEMA_PREFIX + "migration-receipt:v2": "/receipt_digest",
    SCHEMA_PREFIX + "notification-receipt:v3": "/receipt_digest",
    SCHEMA_PREFIX + "public-run-event:v2": "/event_digest",
    SCHEMA_PREFIX + "publication-manifest:v1": "/manifest_digest",
    SCHEMA_PREFIX + "retention-receipt:v2": "/receipt_digest",
    SCHEMA_PREFIX + "source-coverage-receipt:v1": "/receipt_digest",
    SCHEMA_PREFIX + "source-inventory:v1": "/inventory_digest",
}
FINAL_PUBLIC_SELF_POINTERS = {
    schema_id: FINAL_SCHEMA_SELF_POINTERS[schema_id]
    for schema_id in FINAL_AUTO_PUBLIC_SCHEMA_IDS
}
ALL_PUBLIC_SELF_POINTERS = {
    **PUBLIC_SELF_POINTERS,
    **FINAL_PUBLIC_SELF_POINTERS,
}
PRIVATE_SELF_POINTERS = {
    SCHEMA_PREFIX + "lock-state:v1": "/state_digest",
    SCHEMA_PREFIX + "public-queue-envelope:v2": "/envelope_digest",
    SCHEMA_PREFIX + "raw-segment:v2": "/segment_digest",
    SCHEMA_PREFIX + "watermark:v2": "/state_digest",
}
EXPECTED_MECHANISM_INTERFACE_RAW_SHA256 = (
    "0f4837d9cec37c845cd5e9e799b5f572944cf8fe2457e8b95f696db3b9c03998"
)
EXPECTED_AUTO_INTERFACE_RAW_SHA256 = (
    "2c47d6a810a18f878e3935bad9bde42aeb8e7f9c8c51b0ead19acadc48a2b366"
)
BASE_MECHANISM_GIT_OBJECT_ID = "sha1:37d07a47ae87fcf246046d1611d3e00f000d1fa4"
LANES = ("REGISTRY", "RUN_LOG")
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
RUN_LOG_WRITE_PREFIX = "OpenAIDatabase/data/run_logs/skills_runs/"
DAILY_MANIFEST_ID = SCHEMA_PREFIX + "daily-run-shard-manifest:v1"
INDEX_ENTRY_ID = SCHEMA_PREFIX + "run-event-index-entry:v1"
PUBLIC_RUN_EVENT_ID = SCHEMA_PREFIX + "public-run-event:v2"
MAX_RUN_LOG_PART_BYTES = 20 * 1024 * 1024
DAILY_RUN_PATH_RE = re.compile(
    r"^OpenAIDatabase/data/run_logs/skills_runs/"
    r"([0-9]{4})/([0-9]{2})/([0-9]{2})/"
    r"(manifest|index|part)-([0-9]{4})\.(json|jsonl)$"
)
SHARED_GATES = (
    "BUNDLE_DIGEST",
    "EXPECTED_REMOTE_HEAD",
    "LOCK_OWNERSHIP",
    "PATH_BOUNDARY",
    "POLICY_DIGEST",
    "PRIVACY",
)
SURFACE_ROLE = {
    "AGENTS": {"UNKNOWN"},
    "CLAUDE": {"UNKNOWN"},
    "CODEX_AUTOMATION": {"AUTOMATION"},
    "CODEX_CLI": {"CLI"},
    "CODEX_DESKTOP": {"SUBAGENT", "USER"},
}
BASELINE_BREAKDOWN = (
    ("CODEX_AUTOMATION", "AUTOMATION", 46),
    ("CODEX_CLI", "CLI", 8),
    ("CODEX_DESKTOP", "SUBAGENT", 329),
    ("CODEX_DESKTOP", "USER", 176),
)
BASELINE_UNMAPPED = (("LEGACY_THREAD_SOURCE_MISSING", 18),)


@dataclasses.dataclass(frozen=True)
class AutoContract:
    """Composed non-active contract with shared and private registries."""

    shared: ContractBundle
    development: ContractBundle
    interface: Mapping[str, Any]
    mechanism_interface: Mapping[str, Any]


def _fail(code: str) -> None:
    raise ContractError(code)


def _parse_utc(value: str) -> dt.datetime:
    try:
        return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except (TypeError, ValueError) as exc:
        raise ContractError(f"AUTO_UTC_INVALID:{value}") from exc


def _time_order(instance: Mapping[str, Any], first: str, second: str, code: str) -> None:
    if _parse_utc(instance[second]) < _parse_utc(instance[first]):
        _fail(code)


def _bytewise(values: Iterable[str]) -> list[str]:
    return sorted(values, key=lambda value: value.encode("utf-8"))


def _require_sorted_unique(
    items: Sequence[Any],
    key,
    code: str,
) -> None:
    keys = [key(item) for item in items]
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        _fail(f"{code}:SORTED_UNIQUE_REQUIRED")


def _entry_map(
    entries: Any,
    expected: Mapping[str, str],
    visibility: str,
) -> Mapping[str, Mapping[str, Any]]:
    if not isinstance(entries, list) or len(entries) != len(expected):
        _fail(f"AUTO_{visibility}_ENTRY_COUNT_MISMATCH")
    identifiers = [entry.get("id") for entry in entries if isinstance(entry, dict)]
    if identifiers != _bytewise(expected) or len(identifiers) != len(entries):
        _fail(f"AUTO_{visibility}_ENTRY_ORDER_OR_SET_MISMATCH")
    result: Dict[str, Mapping[str, Any]] = {}
    for entry in entries:
        schema_id = entry["id"]
        if (
            entry.get("owner_plane") != "AUTO"
            or entry.get("visibility") != visibility
            or entry.get("self_digest_pointer") != expected[schema_id]
        ):
            _fail(f"AUTO_{visibility}_ENTRY_CONTRACT_MISMATCH:{schema_id}")
        result[schema_id] = entry
    return result


def _schema_digest_field_names(schema: Any) -> set[str]:
    """Return public fields whose declared value is a SHA-256 digest."""

    result: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict):
                for name, child in properties.items():
                    if isinstance(child, dict):
                        reference = child.get("$ref")
                        if reference == (
                            SCHEMA_PREFIX + "common-definitions:v1#/$defs/sha256"
                        ):
                            result.add(name)
                    walk(child)
            for key, child in node.items():
                if key != "properties":
                    walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(schema)
    return result


def _validate_public_digest_field_policy(
    schemas: Mapping[str, Any],
    policies: Mapping[str, Any],
) -> None:
    policy = policies.get(
        "urn:linzecolin:agentdatabase:skillops:policy:public-value:v2"
    )
    if policy is None:
        policy = policies.get(
            "urn:linzecolin:agentdatabase:skillops:policy:public-value:v1"
        )
    if not isinstance(policy, dict):
        _fail("AUTO_PUBLIC_VALUE_POLICY_NOT_TRUSTED")
    allowed = set(policy["allowed_high_entropy_field_names"])
    fields: set[str] = set()
    for schema in schemas.values():
        fields.update(_schema_digest_field_names(schema))
    missing = sorted(fields.difference(allowed))
    if missing:
        _fail("AUTO_PUBLIC_DIGEST_FIELDS_NOT_APPROVED:" + ",".join(missing))


def load_auto_contract() -> AutoContract:
    """Load exact A1a interfaces and construct offline-only registries."""

    mechanism = load_draft_contract()
    mechanism_path = GOVERNANCE_DIR / "draft-interface.json"
    observed_mechanism_digest = hashlib.sha256(mechanism_path.read_bytes()).hexdigest()
    if observed_mechanism_digest != EXPECTED_MECHANISM_INTERFACE_RAW_SHA256:
        _fail("AUTO_MECHANISM_INTERFACE_RAW_DIGEST_MISMATCH")
    mechanism_interface = strict_load(mechanism_path)
    interface = strict_load(AUTO_DIR / "draft-interface.json")
    if (
        interface.get("status") != "DRAFT_NON_ACTIVE"
        or interface.get("activation_forbidden") is not True
        or interface.get("protocol_revision") != PROTOCOL
        or interface.get("base_mechanism_git_object_id") != BASE_MECHANISM_GIT_OBJECT_ID
        or interface.get("mechanism_interface_raw_sha256")
        != EXPECTED_MECHANISM_INTERFACE_RAW_SHA256
        or interface.get("complete_shared_schema_count_after_m0b") != 29
        or interface.get("auto_private_schemas_in_shared_bundle") is not False
        or interface.get("next_phase") != "MECHANISM_M0B"
    ):
        _fail("AUTO_DRAFT_INTERFACE_CONTRACT_MISMATCH")
    if interface.get("auto_public_schema_count") != len(PUBLIC_SELF_POINTERS):
        _fail("AUTO_PUBLIC_SCHEMA_COUNT_MISMATCH")
    if interface.get("auto_private_schema_count") != len(PRIVATE_SELF_POINTERS):
        _fail("AUTO_PRIVATE_SCHEMA_COUNT_MISMATCH")

    public_entries = _entry_map(
        interface.get("auto_public_schema_entries"), PUBLIC_SELF_POINTERS, "PUBLIC"
    )
    private_entries = _entry_map(
        interface.get("auto_private_schema_entries"), PRIVATE_SELF_POINTERS, "PRIVATE"
    )
    public = load_schema_directories([AUTO_DIR / "schemas" / "public"])
    private = load_schema_directories([AUTO_DIR / "schemas" / "private"])
    if set(public) != set(PUBLIC_SELF_POINTERS):
        _fail("AUTO_PUBLIC_SCHEMA_SET_MISMATCH")
    if set(private) != set(PRIVATE_SELF_POINTERS):
        _fail("AUTO_PRIVATE_SCHEMA_SET_MISMATCH")

    for schema_id, schema in {**public, **private}.items():
        entry = public_entries.get(schema_id) or private_entries.get(schema_id)
        if entry is None:
            _fail(f"AUTO_SCHEMA_INTERFACE_ENTRY_MISSING:{schema_id}")
        relative = Path(entry["relative_path"])
        expected_prefix = (
            "CodexSkills/registry/auto/schemas/public/"
            if schema_id in public
            else "CodexSkills/registry/auto/schemas/private/"
        )
        if not entry["relative_path"].startswith(expected_prefix):
            _fail(f"AUTO_SCHEMA_PATH_OWNER_MISMATCH:{schema_id}")
        if (REPO_ROOT / relative).resolve() != (
            AUTO_DIR
            / "schemas"
            / ("public" if schema_id in public else "private")
            / relative.name
        ).resolve():
            _fail(f"AUTO_SCHEMA_PATH_MISMATCH:{schema_id}")
        actual = hashlib.sha256(canonicalize_object(schema)).hexdigest()
        if entry.get("schema_sha256") != actual:
            _fail(f"AUTO_SCHEMA_DIGEST_MISMATCH:{schema_id}")

    shared_schemas = {**mechanism.schemas, **public}
    if len(shared_schemas) != 29 or set(shared_schemas).intersection(private):
        _fail("AUTO_SHARED_BUNDLE_SCHEMA_SET_MISMATCH")
    shared_registry, shared_checker = build_registry(shared_schemas)
    shared_pointers = {**mechanism.self_digest_pointers, **PUBLIC_SELF_POINTERS}
    shared = ContractBundle(
        shared_schemas,
        shared_registry,
        shared_checker,
        shared_pointers,
        mechanism.policies,
        PROTOCOL,
    )

    development_schemas = {**shared_schemas, **private}
    development_registry, development_checker = build_registry(development_schemas)
    development = ContractBundle(
        development_schemas,
        development_registry,
        development_checker,
        {**shared_pointers, **PRIVATE_SELF_POINTERS},
        mechanism.policies,
        PROTOCOL,
    )
    _validate_public_digest_field_policy(public, mechanism.policies)
    return AutoContract(shared, development, interface, mechanism_interface)


def load_trusted_auto_contract(repo_root: Path, trust: TrustTuple) -> AutoContract:
    """Compose Auto-private schemas around an externally trusted shared bundle.

    The candidate/active shared Registry is selected exclusively by the caller's
    repo-external ``TrustTuple``.  The local draft is used only to verify the
    independently versioned Auto-private schemas and the A1a ownership
    interface; it can never confer shared-bundle trust.
    """

    trusted_shared = load_trusted_bundle(repo_root, trust)
    local = load_auto_contract()
    trusted_schema_ids = set(trusted_shared.schemas)
    trusted_policy_ids = set(trusted_shared.policies)
    legacy_profile = (
        trusted_schema_ids == set(local.shared.schemas)
        and trusted_policy_ids == set(local.shared.policies)
    )
    final_profile = (
        trusted_schema_ids == set(FINAL_SCHEMA_SELF_POINTERS)
        and trusted_policy_ids == set(FINAL_POLICY_IDS)
    )
    if not (legacy_profile or final_profile):
        _fail("AUTO_TRUSTED_SHARED_PROFILE_UNSUPPORTED")
    if legacy_profile:
        for schema_id, trusted_schema in trusted_shared.schemas.items():
            if canonicalize_object(trusted_schema) != canonicalize_object(
                local.shared.schemas[schema_id]
            ):
                _fail(
                    f"AUTO_TRUSTED_SHARED_SCHEMA_BYTES_MISMATCH:{schema_id}"
                )
        for policy_id, trusted_policy in trusted_shared.policies.items():
            if canonicalize_object(trusted_policy) != canonicalize_object(
                local.shared.policies[policy_id]
            ):
                _fail(
                    f"AUTO_TRUSTED_POLICY_BYTES_MISMATCH:{policy_id}"
                )
    else:
        local_public_schemas = load_schema_directories(
            [
                AUTO_DIR / "schemas" / "public",
                AUTO_DIR / "schemas" / "public-v2",
            ]
        )
        local_final_public = {
            schema_id: local_public_schemas[schema_id]
            for schema_id in FINAL_PUBLIC_SELF_POINTERS
            if schema_id in local_public_schemas
        }
        if set(local_final_public) != set(FINAL_PUBLIC_SELF_POINTERS):
            _fail("AUTO_FINAL_PUBLIC_SCHEMA_SET_MISMATCH")
        for schema_id in sorted(FINAL_PUBLIC_SELF_POINTERS):
            if canonicalize_object(
                trusted_shared.schemas[schema_id]
            ) != canonicalize_object(local_final_public[schema_id]):
                _fail(
                    f"AUTO_TRUSTED_FINAL_PUBLIC_SCHEMA_BYTES_MISMATCH:{schema_id}"
                )

    object_id = trust.verified_git_object_id.split(":", 1)[1]

    def git_blob(relative_path: str) -> bytes:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_root), "show", f"{object_id}:{relative_path}"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            _fail(f"AUTO_TRUSTED_BLOB_READ_FAILED:{relative_path}")
        if result.returncode != 0:
            _fail(f"AUTO_TRUSTED_BLOB_READ_FAILED:{relative_path}")
        return result.stdout

    trusted_interface_raw = git_blob("CodexSkills/registry/auto/draft-interface.json")
    if hashlib.sha256(trusted_interface_raw).hexdigest() != EXPECTED_AUTO_INTERFACE_RAW_SHA256:
        _fail("AUTO_TRUSTED_INTERFACE_RAW_DIGEST_MISMATCH")
    trusted_interface = parse_json_bytes(trusted_interface_raw)
    if canonicalize_object(trusted_interface) != canonicalize_object(local.interface):
        _fail("AUTO_TRUSTED_INTERFACE_LOCAL_DRIFT")
    private_entries = _entry_map(
        trusted_interface.get("auto_private_schema_entries"),
        PRIVATE_SELF_POINTERS,
        "PRIVATE",
    )
    private = {}
    for schema_id, entry in private_entries.items():
        raw = git_blob(entry["relative_path"])
        schema = parse_json_bytes(raw)
        if not isinstance(schema, dict) or schema.get("$id") != schema_id:
            _fail(f"AUTO_TRUSTED_PRIVATE_SCHEMA_BINDING_MISMATCH:{schema_id}")
        observed_digest = hashlib.sha256(canonicalize_object(schema)).hexdigest()
        if observed_digest != entry["schema_sha256"]:
            _fail(f"AUTO_TRUSTED_PRIVATE_SCHEMA_DIGEST_MISMATCH:{schema_id}")
        private[schema_id] = schema
    development_schemas = {**trusted_shared.schemas, **private}
    development_registry, development_checker = build_registry(development_schemas)
    development = ContractBundle(
        development_schemas,
        development_registry,
        development_checker,
        {**trusted_shared.self_digest_pointers, **PRIVATE_SELF_POINTERS},
        trusted_shared.policies,
        PROTOCOL,
    )
    _validate_public_digest_field_policy(
        {
            schema_id: schema
            for schema_id, schema in trusted_shared.schemas.items()
            if schema_id in ALL_PUBLIC_SELF_POINTERS
        },
        trusted_shared.policies,
    )
    return AutoContract(
        trusted_shared,
        development,
        local.interface,
        local.mechanism_interface,
    )


def _surface_breakdown(items: Sequence[Mapping[str, Any]]) -> Tuple[Tuple[str, str, int], ...]:
    rows = tuple(
        (item["surface_class"], item["actor_role"], item["count"])
        for item in items
    )
    if rows != tuple(sorted(rows)) or len(rows) != len(set(rows)):
        _fail("AUTO_SURFACE_BREAKDOWN_ORDER_OR_UNIQUENESS_INVALID")
    for surface, role, _count in rows:
        if role not in SURFACE_ROLE.get(surface, set()):
            _fail(f"AUTO_SURFACE_ACTOR_ROLE_INVALID:{surface}:{role}")
    return rows


def _reason_counts(items: Sequence[Mapping[str, Any]]) -> Tuple[Tuple[str, int], ...]:
    rows = tuple((item["reason_code"], item["count"]) for item in items)
    if rows != tuple(sorted(rows)) or len(rows) != len(set(rows)):
        _fail("AUTO_REASON_COUNT_ORDER_OR_UNIQUENESS_INVALID")
    return rows


def _validate_source_inventory(instance: Mapping[str, Any]) -> None:
    _time_order(instance, "observed_started_at", "observed_finished_at", "INVENTORY_TIME_ORDER_INVALID")
    exclusions = instance["exclusions"]
    _require_sorted_unique(exclusions, lambda item: item["reason_code"], "INVENTORY_EXCLUSION_ORDER")
    for total, field in (
        (sum(item["node_count"] for item in exclusions), "excluded_node_count"),
        (sum(item["file_count"] for item in exclusions), "excluded_file_count"),
        (sum(item["byte_count"] for item in exclusions), "excluded_bytes"),
    ):
        if total != instance[field]:
            _fail(f"INVENTORY_EXCLUSION_TOTAL_MISMATCH:{field}")
    aliases = instance["symlink_aliases"]
    _require_sorted_unique(aliases, lambda item: item["alias_path"], "INVENTORY_ALIAS_ORDER")
    if instance["symlink_alias_count"] != len(aliases):
        _fail("INVENTORY_ALIAS_COUNT_MISMATCH")
    errors = instance["scan_error_counts"]
    _require_sorted_unique(errors, lambda item: item["reason_code"], "INVENTORY_ERROR_ORDER")
    oversize_errors = sum(
        item["count"] for item in errors if item["reason_code"] == "OVERSIZE_NON_POLICY"
    )
    if instance["oversize_blocked_count"] != oversize_errors:
        _fail("INVENTORY_OVERSIZE_COUNT_MISMATCH")
    complete = instance["completeness_status"] == "COMPLETE_AFTER_POLICY_EXCLUSIONS"
    if complete and (errors or instance["oversize_blocked_count"]):
        _fail("INVENTORY_COMPLETE_WITH_BLOCKING_ERROR")
    if not complete and not errors and instance["completeness_status"] == "INCOMPLETE":
        _fail("INVENTORY_INCOMPLETE_WITHOUT_ENUMERATED_ERROR")


def _validate_public_run_event(instance: Mapping[str, Any]) -> None:
    surface = instance["surface_class"]
    role = instance["actor_role"]
    if role not in SURFACE_ROLE.get(surface, set()):
        _fail(f"RUN_EVENT_SURFACE_ACTOR_ROLE_INVALID:{surface}:{role}")
    if instance["binding_state"] == "BOUND" and surface not in {
        "CODEX_AUTOMATION",
        "CODEX_CLI",
    }:
        _fail("RUN_EVENT_BOUND_SURFACE_INELIGIBLE")
    if instance["binding_state"] == "BOUND":
        controlled = instance["controlled_invocation"]
        if controlled["surface_class"] != surface:
            _fail("RUN_EVENT_CONTROLLED_SURFACE_MISMATCH")
        if _parse_utc(controlled["observed_at"]) > _parse_utc(instance["occurred_at"]):
            _fail("RUN_EVENT_INVOCATION_EVIDENCE_AFTER_EVENT")
    if instance["event_type"] == "BINDING_CORRECTION":
        if instance["supersedes_event_uid"] == instance["event_uid"]:
            _fail("RUN_EVENT_CANNOT_SUPERSEDE_SELF")
    metrics = instance["metrics"]
    measured = metrics["token_usage_status"] == "MEASURED"
    token_values = (metrics["input_tokens"], metrics["output_tokens"])
    if measured != all(value is not None for value in token_values):
        _fail("RUN_EVENT_TOKEN_MEASUREMENT_STATE_MISMATCH")
    if not measured and any(value is not None for value in token_values):
        _fail("RUN_EVENT_UNMEASURED_TOKENS_MUST_BE_NULL")


def _sydney_date(value: str) -> str:
    return _parse_utc(value).replace(
        tzinfo=dt.timezone.utc
    ).astimezone(ZoneInfo("Australia/Sydney")).date().isoformat()


def _parse_daily_run_path(path: str) -> Tuple[str, int]:
    match = DAILY_RUN_PATH_RE.fullmatch(path)
    if match is None:
        _fail(f"PUBLICATION_RUN_LOG_PATH_INVALID:{path}")
    try:
        local_date = dt.date(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
        )
    except ValueError as exc:
        raise ContractError(
            f"PUBLICATION_RUN_LOG_DATE_INVALID:{path}"
        ) from exc
    if local_date.isoformat() != "-".join(
        match.group(index) for index in (1, 2, 3)
    ):
        _fail(f"PUBLICATION_RUN_LOG_DATE_NONCANONICAL:{path}")
    kind = match.group(4)
    number = int(match.group(5))
    extension = match.group(6)
    if number < 1 or number > 9999:
        _fail(f"PUBLICATION_RUN_LOG_SEQUENCE_INVALID:{path}")
    if (kind == "manifest") != (extension == "json"):
        _fail(f"PUBLICATION_RUN_LOG_EXTENSION_INVALID:{path}")
    return kind, number


def _validate_daily_manifest(instance: Mapping[str, Any]) -> None:
    parts = instance["parts"]
    numbers = [part["part_number"] for part in parts]
    if (
        numbers != list(range(1, len(parts) + 1))
        or numbers[-1] > 9999
    ):
        _fail("DAILY_MANIFEST_PART_NUMBERS_NOT_CONTIGUOUS")
    if instance["manifest_revision"] > 9999:
        _fail("DAILY_MANIFEST_REVISION_EXCEEDS_PATH_WIDTH")
    if instance["max_part_number"] != numbers[-1]:
        _fail("DAILY_MANIFEST_MAX_PART_NUMBER_MISMATCH")
    if instance["total_part_count"] != len(parts):
        _fail("DAILY_MANIFEST_TOTAL_PART_COUNT_MISMATCH")

    active = [part for part in parts if part["state"] == "ACTIVE"]
    pruned = [part for part in parts if part["state"] == "PRUNED"]
    if instance["manifest_revision"] == 1 and pruned:
        _fail("DAILY_MANIFEST_REVISION_ONE_CANNOT_CONTAIN_PRUNED_PART")
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

    publication_at = _parse_utc(
        instance["publication_transaction_at"]
    ).replace(tzinfo=dt.timezone.utc)
    for part in parts:
        number = part["part_number"]
        if part["shard_name"] != f"part-{number:04d}.jsonl":
            _fail("DAILY_MANIFEST_SHARD_NAME_NUMBER_MISMATCH")
        if part["index_name"] != f"index-{number:04d}.jsonl":
            _fail("DAILY_MANIFEST_INDEX_NAME_NUMBER_MISMATCH")
        if part["shard_bytes"] > MAX_RUN_LOG_PART_BYTES:
            _fail("DAILY_MANIFEST_SHARD_SIZE_EXCEEDED")
        if part["index_bytes"] > MAX_RUN_LOG_PART_BYTES:
            _fail("DAILY_MANIFEST_INDEX_SIZE_EXCEEDED")
        if part["record_count"] != part["index_record_count"]:
            _fail("DAILY_MANIFEST_INDEX_RECORD_COUNT_MISMATCH")
        first_key = (
            _parse_utc(part["first_occurred_at"]),
            part["first_event_uid"],
        )
        last_key = (
            _parse_utc(part["last_occurred_at"]),
            part["last_event_uid"],
        )
        if first_key > last_key:
            _fail("DAILY_MANIFEST_EVENT_RANGE_REVERSED")
        if (
            _sydney_date(part["first_occurred_at"])
            != instance["local_date"]
            or _sydney_date(part["last_occurred_at"])
            != instance["local_date"]
        ):
            _fail("DAILY_MANIFEST_SYDNEY_DATE_MISMATCH")
        first_published = _parse_utc(
            part["first_published_at"]
        ).replace(tzinfo=dt.timezone.utc)
        retention_anchor = _parse_utc(
            part["retention_not_before"]
        ).replace(tzinfo=dt.timezone.utc)
        if first_published < last_key[0].replace(
            tzinfo=dt.timezone.utc
        ):
            _fail("DAILY_MANIFEST_PUBLISHED_BEFORE_EVENT")
        if publication_at < first_published:
            _fail("DAILY_MANIFEST_REVISION_BEFORE_FIRST_PUBLICATION")
        if retention_anchor != first_published + dt.timedelta(days=365):
            _fail("DAILY_MANIFEST_RETENTION_ANCHOR_NOT_EXACT_365D")
        if part["state"] == "PRUNED":
            pruned_at = _parse_utc(part["pruned_at"]).replace(
                tzinfo=dt.timezone.utc
            )
            if pruned_at <= retention_anchor:
                _fail("DAILY_MANIFEST_PRUNE_NOT_STRICTLY_AFTER_ANCHOR")
            if pruned_at > publication_at:
                _fail(
                    "DAILY_MANIFEST_PRUNE_AFTER_REVISION_PUBLICATION"
                )


def _validate_index_entry(instance: Mapping[str, Any]) -> None:
    if _parse_utc(instance["first_published_at"]) < _parse_utc(
        instance["occurred_at"]
    ):
        _fail("RUN_EVENT_INDEX_PUBLISHED_BEFORE_OCCURRED")
    if instance["event_type"] == "BINDING_CORRECTION":
        if (
            instance["event_uid"] == instance["supersedes_event_uid"]
            or instance["event_digest"]
            == instance["supersedes_event_digest"]
        ):
            _fail("RUN_EVENT_INDEX_CORRECTION_SELF_REFERENCE")


def _validate_source_coverage(instance: Mapping[str, Any]) -> None:
    _time_order(
        instance,
        "observation_window_started_at",
        "observation_window_finished_at",
        "COVERAGE_WINDOW_TIME_ORDER_INVALID",
    )
    if _parse_utc(instance["heartbeat_at"]) < _parse_utc(instance["observation_window_finished_at"]):
        _fail("COVERAGE_HEARTBEAT_PRECEDES_WINDOW_END")
    reason_codes = instance["reason_codes"]
    if reason_codes != _bytewise(reason_codes) or len(reason_codes) != len(set(reason_codes)):
        _fail("COVERAGE_REASON_CODE_ORDER_OR_UNIQUENESS_INVALID")
    if instance["coverage_subject"] == "SKILL_SOURCE":
        inventory_fields = {
            "inventory_uid",
            "inventory_digest",
            "inventory_completeness_status",
            "source_material_policy_id",
            "source_material_policy_digest",
        }
        present = inventory_fields.intersection(instance)
        if present and present != inventory_fields:
            _fail("COVERAGE_INVENTORY_REFERENCE_PARTIAL")
        if instance["coverage_state"] == "UNKNOWN" and present:
            if instance["inventory_completeness_status"] != "INCOMPLETE":
                _fail("COVERAGE_UNKNOWN_INVENTORY_MUST_BE_INCOMPLETE")
        if instance["coverage_state"] != "COVERED" and not reason_codes:
            _fail("COVERAGE_NON_COVERED_REASON_REQUIRED")
        if instance["coverage_state"] == "COVERED" and reason_codes:
            _fail("COVERAGE_COVERED_REASON_MUST_BE_EMPTY")
        return

    if instance["input_record_count"] != sum(
        instance[field]
        for field in (
            "mapped_input_record_count",
            "unmapped_record_count",
            "policy_excluded_record_count",
            "quarantined_input_record_count",
        )
    ):
        _fail("COVERAGE_INPUT_RECONCILIATION_MISMATCH")
    if instance["observed_run_count"] != sum(
        instance[field]
        for field in (
            "projected_bound_run_count",
            "projected_unknown_run_count",
            "quarantined_run_count",
        )
    ):
        _fail("COVERAGE_RUN_RECONCILIATION_MISMATCH")
    if instance["projected_event_count"] != (
        instance["projected_bound_run_count"] + instance["projected_unknown_run_count"]
    ):
        _fail("COVERAGE_PROJECTED_EVENT_COUNT_MISMATCH")
    breakdown = _surface_breakdown(instance["surface_breakdown"])
    unmapped = _reason_counts(instance["unmapped_reasons"])
    if sum(row[2] for row in breakdown) != instance["mapped_input_record_count"]:
        _fail("COVERAGE_SURFACE_BREAKDOWN_TOTAL_MISMATCH")
    if sum(row[1] for row in unmapped) != instance["unmapped_record_count"]:
        _fail("COVERAGE_UNMAPPED_REASON_TOTAL_MISMATCH")
    if instance["coverage_state"] == "COVERED" and any(
        instance[field]
        for field in (
            "unmapped_record_count",
            "quarantined_input_record_count",
            "quarantined_run_count",
        )
    ):
        _fail("COVERAGE_COVERED_WITH_UNSETTLED_RECORDS")
    if instance["coverage_state"] != "COVERED" and not reason_codes:
        _fail("COVERAGE_NON_COVERED_REASON_REQUIRED")
    if instance["coverage_state"] == "COVERED" and reason_codes:
        _fail("COVERAGE_COVERED_REASON_MUST_BE_EMPTY")
    if "baseline_action_code" in instance:
        if (
            instance["input_record_count"] != 577
            or instance["mapped_input_record_count"] != 559
            or instance["unmapped_record_count"] != 18
            or instance["policy_excluded_record_count"] != 0
            or instance["quarantined_input_record_count"] != 0
            or breakdown != BASELINE_BREAKDOWN
            or unmapped != BASELINE_UNMAPPED
            or instance["coverage_state"] != "UNKNOWN"
            or instance["historical_public_run_event_count"] != 0
            or "BASELINE_ONLY" not in reason_codes
        ):
            _fail("COVERAGE_BASELINE_CONTRACT_MISMATCH")


def _validate_auto_receipt(instance: Mapping[str, Any]) -> None:
    _time_order(instance, "started_at", "finished_at", "AUTO_RECEIPT_TIME_ORDER_INVALID")
    lanes = instance["lane_results"]
    _require_sorted_unique(lanes, lambda item: item["lane"], "AUTO_RECEIPT_LANE_ORDER")
    if tuple(item["lane"] for item in lanes) != LANES:
        _fail("AUTO_RECEIPT_LANE_SET_INCOMPLETE")
    settled = instance["settled_lanes"]
    if settled != _bytewise(settled) or len(settled) != len(set(settled)):
        _fail("AUTO_RECEIPT_SETTLED_LANE_ORDER_INVALID")
    reason_codes = instance["reason_codes"]
    if reason_codes != _bytewise(reason_codes) or len(reason_codes) != len(set(reason_codes)):
        _fail("AUTO_RECEIPT_REASON_CODE_ORDER_INVALID")
    actual_settled = [item["lane"] for item in lanes if item["status"] == "SETTLED"]
    if settled != actual_settled:
        _fail("AUTO_RECEIPT_SETTLED_LANE_RESULT_MISMATCH")
    for lane in lanes:
        if lane["published_count"] + lane["quarantined_count"] > lane["input_count"]:
            _fail(f"AUTO_RECEIPT_LANE_COUNT_INVALID:{lane['lane']}")
        if lane["status"] == "NO_CHANGE" and (
            lane["published_count"] or lane["quarantined_count"]
        ):
            _fail(f"AUTO_RECEIPT_NO_CHANGE_HAS_OUTPUT:{lane['lane']}")
        if lane["status"] == "SETTLED" and lane["quarantined_count"]:
            _fail(f"AUTO_RECEIPT_SETTLED_HAS_QUARANTINE:{lane['lane']}")
    has_publication = "publication" in instance
    if has_publication != (instance["final_action"] == "PUBLISH"):
        _fail("AUTO_RECEIPT_PUBLICATION_ACTION_MISMATCH")
    if bool(settled) != has_publication:
        _fail("AUTO_RECEIPT_PUBLICATION_SETTLEMENT_MISMATCH")
    statuses = {lane["status"] for lane in lanes}
    if instance["overall_status"] == "SUCCESS":
        if not settled or not statuses.issubset({"NO_CHANGE", "SETTLED"}):
            _fail("AUTO_RECEIPT_SUCCESS_LANE_STATUS_INVALID")
    if instance["overall_status"] == "NO_CHANGE" and statuses != {"NO_CHANGE"}:
        _fail("AUTO_RECEIPT_NO_CHANGE_LANE_STATUS_INVALID")
    if instance["overall_status"] == "PARTIAL":
        if not settled or statuses.issubset({"NO_CHANGE", "SETTLED"}):
            _fail("AUTO_RECEIPT_PARTIAL_LANE_STATUS_INVALID")


def _validate_artifact_target(lane: str, schema_id: str, path: str) -> None:
    if schema_id not in EXPECTED_SCHEMA_SELF_POINTERS:
        _fail(f"PUBLICATION_ARTIFACT_SCHEMA_NOT_IN_SHARED_BUNDLE:{schema_id}")
    if lane == "RUN_LOG":
        if schema_id != SCHEMA_PREFIX + "public-run-event:v2":
            _fail(f"PUBLICATION_RUN_LOG_SCHEMA_INVALID:{schema_id}")
        if not path.startswith(RUN_LOG_WRITE_PREFIX):
            _fail(f"PUBLICATION_RUN_LOG_PATH_INVALID:{path}")
        return
    if not (
        path in REGISTRY_CONTROL_PATHS
        or any(path.startswith(prefix) for prefix in REGISTRY_WRITE_PREFIXES)
    ):
        _fail(f"PUBLICATION_REGISTRY_PATH_INVALID:{path}")


def _validate_publication_manifest(instance: Mapping[str, Any]) -> None:
    lanes = instance["lane_manifests"]
    _require_sorted_unique(lanes, lambda item: item["lane"], "PUBLICATION_LANE_ORDER")
    if instance["settled_lanes"] != [item["lane"] for item in lanes]:
        _fail("PUBLICATION_SETTLED_LANE_MISMATCH")
    all_artifact_uids = []
    for lane in lanes:
        artifacts = lane["artifacts"]
        if lane["artifact_count"] != len(artifacts) or not artifacts:
            _fail(f"PUBLICATION_ARTIFACT_COUNT_MISMATCH:{lane['lane']}")
        _require_sorted_unique(
            artifacts,
            lambda item: (item["artifact_repo_path"], item["artifact_uid"]),
            f"PUBLICATION_ARTIFACT_ORDER:{lane['lane']}",
        )
        for artifact in artifacts:
            all_artifact_uids.append(artifact["artifact_uid"])
            _validate_artifact_target(
                lane["lane"],
                artifact["artifact_schema_id"],
                artifact["artifact_repo_path"],
            )
    if len(all_artifact_uids) != len(set(all_artifact_uids)):
        _fail("PUBLICATION_ARTIFACT_UID_DUPLICATE")
    gates = instance["shared_gates"]
    _require_sorted_unique(gates, lambda item: item["gate_code"], "PUBLICATION_GATE_ORDER")
    if tuple(item["gate_code"] for item in gates) != SHARED_GATES:
        _fail("PUBLICATION_SHARED_GATE_SET_INCOMPLETE")


def _validate_notification_receipt(instance: Mapping[str, Any]) -> None:
    status = instance["provider_status"]
    timing = instance["timing"]
    if (status == "NOT_REQUIRED") != (timing == "NOT_REQUIRED"):
        _fail("NOTIFICATION_NOT_REQUIRED_STATE_MISMATCH")
    if instance["impact"] == "MAJOR" and timing == "NOT_REQUIRED":
        _fail("NOTIFICATION_MAJOR_CANNOT_BE_NOT_REQUIRED")
    if status == "SENT":
        _time_order(instance, "created_at", "sent_at", "NOTIFICATION_SENT_BEFORE_CREATED")


def _validate_retention_receipt(instance: Mapping[str, Any]) -> None:
    _time_order(instance, "cutoff_at", "executed_at", "RETENTION_CUTOFF_AFTER_EXECUTION")
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
    if instance["ttl_breach"]:
        if (
            instance.get("gap_code") != "OFFLINE_TTL_BREACH"
            or instance["offline_duration_seconds"] == 0
            or instance["action"] != "OFFLINE_TTL_BREACH_CLEANUP"
        ):
            _fail("RETENTION_TTL_BREACH_EVIDENCE_INCOMPLETE")
    elif instance.get("gap_code") == "OFFLINE_TTL_BREACH":
        _fail("RETENTION_OFFLINE_GAP_WITHOUT_TTL_BREACH")
    if instance["reprojection_status"] == "FAILED_GAP_RECORDED" and "gap_code" not in instance:
        _fail("RETENTION_FAILED_REPROJECTION_GAP_CODE_REQUIRED")
    if instance.get("gap_code") == "RAW_EXPIRED_UNPUBLISHED" and instance[
        "reprojection_status"
    ] != "FAILED_GAP_RECORDED":
        _fail("RETENTION_RAW_GAP_REPROJECTION_STATE_INVALID")
    if instance["scope"] == "GIT_CURRENT_TREE" and instance["action"] in {
        "DELETE_OWNED_SEGMENT",
        "OFFLINE_TTL_BREACH_CLEANUP",
    }:
        _fail("RETENTION_RAW_ACTION_ON_GIT_SCOPE")
    if instance["scope"] == "MANAGED_RAW" and instance["action"] == "PRUNE_CURRENT_TREE":
        _fail("RETENTION_GIT_ACTION_ON_RAW_SCOPE")


def _validate_retention_receipt_v3(instance: Mapping[str, Any]) -> None:
    _validate_retention_receipt(instance)
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
        executed_at = _parse_utc(instance["executed_at"]).replace(
            tzinfo=dt.timezone.utc
        )
        deadline_breached = False
        for item in affected:
            kind, number = _parse_daily_run_path(
                item["artifact_repo_path"]
            )
            if kind != "part":
                _fail("RETENTION_AFFECTED_ARTIFACT_NOT_PART")
            index_kind, index_number = _parse_daily_run_path(
                item["retained_index_path"]
            )
            if index_kind != "index" or index_number != number:
                _fail("RETENTION_RETAINED_INDEX_PAIR_MISMATCH")
            if item["artifact_repo_path"].rsplit("/", 1)[0] != item[
                "retained_index_path"
            ].rsplit("/", 1)[0]:
                _fail("RETENTION_RETAINED_INDEX_DATE_MISMATCH")
            first_published = _parse_utc(
                item["first_published_at"]
            ).replace(tzinfo=dt.timezone.utc)
            anchor = _parse_utc(
                item["retention_not_before"]
            ).replace(tzinfo=dt.timezone.utc)
            deadline = _parse_utc(item["prune_deadline_at"]).replace(
                tzinfo=dt.timezone.utc
            )
            if anchor != first_published + dt.timedelta(days=365):
                _fail("RETENTION_ANCHOR_NOT_EXACT_365D")
            if deadline != anchor + dt.timedelta(hours=24):
                _fail(
                    "RETENTION_PRUNE_DEADLINE_NOT_24H_AFTER_ANCHOR"
                )
            if executed_at <= anchor:
                _fail(
                    "RETENTION_EXECUTION_NOT_STRICTLY_AFTER_ANCHOR"
                )
            if executed_at > deadline:
                deadline_breached = True
        if instance["prune_deadline_breached"] is not deadline_breached:
            _fail(
                "RETENTION_PRUNE_DEADLINE_BREACH_STATE_MISMATCH"
            )
        if deadline_breached:
            if (
                instance.get("gap_code")
                != "GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH"
            ):
                _fail(
                    "RETENTION_PRUNE_DEADLINE_BREACH_GAP_REQUIRED"
                )
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


def _validate_migration_receipt(instance: Mapping[str, Any]) -> None:
    breakdown = _surface_breakdown(instance["surface_breakdown"])
    unmapped = _reason_counts(instance["unmapped_reasons"])
    if (
        instance["baseline_action_code"]
        != "BASELINE_ESTABLISHED_NO_HISTORICAL_BACKFILL"
        or instance["coverage_state"] != "UNKNOWN"
        or instance["input_record_count"] != 577
        or instance["mapped_input_record_count"] != 559
        or instance["unmapped_record_count"] != 18
        or instance["policy_excluded_record_count"] != 0
        or instance["quarantined_input_record_count"] != 0
        or breakdown != BASELINE_BREAKDOWN
        or unmapped != BASELINE_UNMAPPED
        or instance["historical_public_run_event_count"] != 0
        or instance["private_exact_cursor_stored"] is not True
        or instance["legacy_local_mutation_performed"] is not False
    ):
        _fail("MIGRATION_BASELINE_CONTRACT_MISMATCH")
    if instance["input_record_count"] != (
        instance["mapped_input_record_count"]
        + instance["unmapped_record_count"]
        + instance["policy_excluded_record_count"]
        + instance["quarantined_input_record_count"]
    ):
        _fail("MIGRATION_INPUT_RECONCILIATION_MISMATCH")


def _validate_queue_envelope(instance: Mapping[str, Any]) -> None:
    _validate_artifact_target(
        instance["lane"], instance["artifact_schema_id"], instance["artifact_repo_path"]
    )
    if instance["queue_state"] == "SETTLED" and instance["retry_count"]:
        _fail("QUEUE_SETTLED_RETRY_COUNT_NONZERO")


def _validate_watermark(instance: Mapping[str, Any]) -> None:
    lanes = instance["lane_states"]
    _require_sorted_unique(lanes, lambda item: item["lane"], "WATERMARK_LANE_ORDER")
    if tuple(item["lane"] for item in lanes) != LANES:
        _fail("WATERMARK_LANE_SET_INCOMPLETE")
    for lane in lanes:
        manifest = lane["last_settled_manifest_digest"]
        remote = lane["last_settled_remote_head"]
        if (manifest is None) != (remote is None):
            _fail(f"WATERMARK_SETTLEMENT_EVIDENCE_PARTIAL:{lane['lane']}")


def _validate_lock_state(instance: Mapping[str, Any]) -> None:
    _time_order(instance, "acquired_at", "heartbeat_at", "LOCK_HEARTBEAT_PRECEDES_ACQUIRE")
    _time_order(instance, "heartbeat_at", "lease_expires_at", "LOCK_LEASE_PRECEDES_HEARTBEAT")
    if instance["status"] == "RELEASED":
        if "released_at" not in instance:
            _fail("LOCK_RELEASE_TIME_REQUIRED")
        _time_order(instance, "acquired_at", "released_at", "LOCK_RELEASE_PRECEDES_ACQUIRE")
    elif "released_at" in instance:
        _fail("LOCK_HELD_MUST_NOT_HAVE_RELEASE_TIME")


def _validate_raw_segment(instance: Mapping[str, Any]) -> None:
    _time_order(instance, "created_at", "sealed_at", "RAW_SEGMENT_SEAL_PRECEDES_CREATE")
    _time_order(instance, "sealed_at", "expires_at", "RAW_SEGMENT_EXPIRY_PRECEDES_SEAL")
    if instance["persistence_mode"] == "DISABLED" and (
        instance["record_count"] or instance["byte_count"]
    ):
        _fail("RAW_DISABLED_WITH_PERSISTED_CONTENT")


AUTO_SEMANTIC_VALIDATORS = {
    SCHEMA_PREFIX + "auto-receipt:v2": _validate_auto_receipt,
    DAILY_MANIFEST_ID: _validate_daily_manifest,
    INDEX_ENTRY_ID: _validate_index_entry,
    SCHEMA_PREFIX + "migration-receipt:v2": _validate_migration_receipt,
    SCHEMA_PREFIX + "notification-receipt:v3": _validate_notification_receipt,
    SCHEMA_PREFIX + "public-run-event:v2": _validate_public_run_event,
    SCHEMA_PREFIX + "publication-manifest:v1": _validate_publication_manifest,
    SCHEMA_PREFIX + "retention-receipt:v2": _validate_retention_receipt,
    SCHEMA_PREFIX + "retention-receipt:v3": _validate_retention_receipt_v3,
    SCHEMA_PREFIX + "source-coverage-receipt:v1": _validate_source_coverage,
    SCHEMA_PREFIX + "source-inventory:v1": _validate_source_inventory,
    SCHEMA_PREFIX + "lock-state:v1": _validate_lock_state,
    SCHEMA_PREFIX + "public-queue-envelope:v2": _validate_queue_envelope,
    SCHEMA_PREFIX + "raw-segment:v2": _validate_raw_segment,
    SCHEMA_PREFIX + "watermark:v2": _validate_watermark,
}


def validate_auto_instance(
    contract: AutoContract,
    instance: Any,
    schema_id: str,
    *,
    expected_bundle_digest: Optional[str] = None,
    verify_digest: bool = True,
) -> None:
    """Validate structure, contextual digest, self digest, privacy, and semantics."""

    if schema_id not in AUTO_SEMANTIC_VALIDATORS:
        _fail(f"AUTO_SCHEMA_ID_UNKNOWN:{schema_id}")
    public = schema_id in ALL_PUBLIC_SELF_POINTERS
    validate_instance(
        contract.development,
        instance,
        schema_id,
        expected_bundle_digest=expected_bundle_digest,
        public=public,
        verify_digest=verify_digest,
    )
    AUTO_SEMANTIC_VALIDATORS[schema_id](instance)


def _main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("lint-draft")
    validate = commands.add_parser("validate")
    validate.add_argument("--instance", type=Path, required=True)
    validate.add_argument("--schema-id", required=True)
    validate.add_argument("--expected-bundle-digest", required=True)
    args = parser.parse_args(argv)
    contract = load_auto_contract()
    if args.command == "lint-draft":
        print(
            "AUTO_DRAFT_VALID "
            f"shared_schemas={len(contract.shared.schemas)} "
            f"private_schemas={len(PRIVATE_SELF_POINTERS)} "
            f"policies={len(contract.shared.policies)}"
        )
        return 0
    validate_auto_instance(
        contract,
        strict_load(args.instance),
        args.schema_id,
        expected_bundle_digest=args.expected_bundle_digest,
    )
    print("AUTO_ARTIFACT_VALID")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except (ContractError, CanonicalizationError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
