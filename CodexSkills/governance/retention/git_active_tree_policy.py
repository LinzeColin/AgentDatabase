"""Pure M-063 Git current-tree 365-day retention policy.

The policy consumes exact public-safe daily manifests, shards, retained
indexes, and retention receipts.  It validates the complete append-only
manifest history for one Sydney day, classifies each active shard against an
elapsed 365x24-hour UTC boundary, and emits a public-safe observation and
non-mutating prune plan.

The Auto plane still owns repository reads, publication, deletion, state, and
remote verification.  This module receives immutable bytes only.  It has no
filesystem, Git, network, queue, lock, watermark, or executor capability and
never claims that current-tree pruning erases Git history.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import re
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from CodexSkills.governance.tools.canonical_json import (
    CanonicalizationError,
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_au040_semantic_acceptance import (
    AU040AcceptanceContract,
    ContractError as AU040ContractError,
    validate_daily_manifest_semantics,
    validate_manifest_revision_chain,
    validate_part_index_manifest_closure,
    validate_prune_transaction_closure,
    validate_public_value_v2,
    validate_publication_artifact_set,
    validate_retained_index_manifest_closure,
    validate_retention_receipt_semantics,
)
from CodexSkills.governance.tools.validate_mechanism import (
    ContractBundle,
    ContractError,
    build_registry,
    validate_instance,
)


SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
PROTOCOL_REVISION = (
    "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
)
DAILY_MANIFEST_SCHEMA_ID = (
    SCHEMA_PREFIX + "daily-run-shard-manifest:v1"
)
INDEX_ENTRY_SCHEMA_ID = SCHEMA_PREFIX + "run-event-index-entry:v1"
PUBLIC_RUN_EVENT_SCHEMA_ID = SCHEMA_PREFIX + "public-run-event:v2"
PUBLICATION_MANIFEST_SCHEMA_ID = (
    SCHEMA_PREFIX + "publication-manifest:v2"
)
RETENTION_RECEIPT_SCHEMA_ID = (
    SCHEMA_PREFIX + "retention-receipt:v3"
)
OBSERVATION_SCHEMA_ID = (
    SCHEMA_PREFIX + "git-active-tree-retention-observation:v1"
)
PLAN_SCHEMA_ID = SCHEMA_PREFIX + "git-active-tree-prune-plan:v1"
OBSERVATION_SELF_POINTER = "/evidence_bundle_digest"
PLAN_SELF_POINTER = "/evidence_bundle_digest"

RETENTION_POLICY_ID = (
    "urn:linzecolin:agentdatabase:skillops:policy:retention:v3"
)
RETENTION_POLICY_SHA256 = (
    "bcad1e50a847e040d1350ca2fd977503b4ae642deabd727266e9dbbd26acb7ce"
)
RUN_LOG_ROOT = "OpenAIDatabase/data/run_logs/skills_runs"
JSONL_SERIALIZATION = "RFC8785_JCS_PER_LINE_LF"
OBJECT_SERIALIZATION = "RFC8785_JCS_OBJECT"
MAX_PART_BYTES = 20 * 1024 * 1024
MAX_OBJECT_BYTES = 1024 * 1024
RETENTION_ELAPSED = dt.timedelta(days=365)
PRUNE_DEADLINE = dt.timedelta(hours=24)
RETENTION_MICROSECONDS = 365 * 24 * 60 * 60 * 1_000_000

UTC_Z_RE = re.compile(
    r"^[0-9]{4}-(?:0[1-9]|1[0-2])-"
    r"(?:0[1-9]|[12][0-9]|3[01])T"
    r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:"
    r"[0-5][0-9]\.[0-9]{6}Z$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MANIFEST_PATH_RE = re.compile(
    r"^OpenAIDatabase/data/run_logs/skills_runs/"
    r"(?P<year>[0-9]{4})/(?P<month>0[1-9]|1[0-2])/"
    r"(?P<day>0[1-9]|[12][0-9]|3[01])/"
    r"manifest-(?P<number>[0-9]{4})\.json$"
)
PART_PATH_RE = re.compile(
    r"^OpenAIDatabase/data/run_logs/skills_runs/"
    r"(?P<year>[0-9]{4})/(?P<month>0[1-9]|1[0-2])/"
    r"(?P<day>0[1-9]|[12][0-9]|3[01])/"
    r"part-(?P<number>[0-9]{4})\.jsonl$"
)
INDEX_PATH_RE = re.compile(
    r"^OpenAIDatabase/data/run_logs/skills_runs/"
    r"(?P<year>[0-9]{4})/(?P<month>0[1-9]|1[0-2])/"
    r"(?P<day>0[1-9]|[12][0-9]|3[01])/"
    r"index-(?P<number>[0-9]{4})\.jsonl$"
)
RECEIPT_PATH_RE = re.compile(
    r"^OpenAIDatabase/data/run_logs/skills_runs/"
    r"(?P<year>[0-9]{4})/(?P<month>0[1-9]|1[0-2])/"
    r"(?P<day>0[1-9]|[12][0-9]|3[01])/"
    r"retention-receipt-(?P<number>[0-9]{4})\.json$"
)

KEEP_ACTION_ORDER = (
    "RETAIN_FULL_ACTIVE_SHARDS",
    "RETAIN_ALL_INDEXES",
    "RETAIN_APPEND_ONLY_MANIFEST_HISTORY",
)
PRUNE_ACTION_ORDER = (
    "REVALIDATE_MANIFEST_HISTORY",
    "REVALIDATE_ELIGIBLE_SHARD_AND_RETAINED_INDEX_BYTES",
    "BUILD_RETENTION_RECEIPT_BYTES",
    "BUILD_SUCCESSOR_MANIFEST_BYTES",
    "SETTLE_SINGLE_GIT_TRANSACTION",
    "VERIFY_REMOTE_ACTIVE_TREE",
)


class GitActiveTreePolicyError(ValueError):
    """The M-063 active-tree evidence or policy failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclasses.dataclass(frozen=True)
class GitActiveTreePolicyContext:
    """Exact AU-040 semantics plus bundle-external M-063 evidence schemas."""

    acceptance: AU040AcceptanceContract
    evidence_bundle: ContractBundle


@dataclasses.dataclass(frozen=True)
class DailyTreeMaterial:
    """Validated immutable material for one latest Sydney daily tree."""

    manifest_history: Tuple[Tuple[str, Mapping[str, Any]], ...]
    latest_manifest_path: str
    latest_manifest: Mapping[str, Any]
    part_bytes: Mapping[str, bytes]
    index_bytes: Mapping[str, bytes]
    receipts: Mapping[str, Mapping[str, Any]]


@dataclasses.dataclass(frozen=True)
class GitActiveTreePolicyResult:
    """Canonical observation and non-mutating action plan."""

    canonical_observation_bytes: bytes
    observation_digest: str
    canonical_plan_bytes: bytes
    plan_digest: str
    keep_part_numbers: Tuple[int, ...]
    eligible_part_numbers: Tuple[int, ...]
    already_pruned_part_numbers: Tuple[int, ...]


def _fail(code: str) -> None:
    raise GitActiveTreePolicyError(code)


def _strict_utc(value: Any, code: str) -> dt.datetime:
    if not isinstance(value, str) or UTC_Z_RE.fullmatch(value) is None:
        _fail(code)
    try:
        parsed = dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as exc:
        raise GitActiveTreePolicyError(code) from exc
    return parsed.replace(tzinfo=dt.timezone.utc)


def _format_utc(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )


def _elapsed_microseconds(delta: dt.timedelta) -> int:
    return (
        (delta.days * 86400 + delta.seconds) * 1_000_000
        + delta.microseconds
    )


def _date_from_match(
    match: re.Match[str],
    code: str,
) -> str:
    try:
        value = dt.date(
            int(match.group("year")),
            int(match.group("month")),
            int(match.group("day")),
        )
    except ValueError as exc:
        raise GitActiveTreePolicyError(code) from exc
    return value.isoformat()


def _parse_object(
    raw: bytes,
    *,
    maximum_bytes: int,
    code: str,
) -> Mapping[str, Any]:
    if (
        not isinstance(raw, bytes)
        or not raw
        or len(raw) > maximum_bytes
        or raw.startswith(b"\xef\xbb\xbf")
        or b"\r" in raw
        or raw.endswith(b"\n")
    ):
        _fail(code + "_FRAMING_INVALID")
    try:
        value = parse_json_bytes(raw)
    except CanonicalizationError as exc:
        raise GitActiveTreePolicyError(code + "_JSON_INVALID") from exc
    if not isinstance(value, dict) or canonicalize_object(value) != raw:
        _fail(code + "_JCS_INVALID")
    return value


def _parse_jsonl(
    raw: bytes,
    *,
    code: str,
) -> Tuple[Mapping[str, Any], ...]:
    if (
        not isinstance(raw, bytes)
        or not raw
        or len(raw) > MAX_PART_BYTES
        or not raw.endswith(b"\n")
        or raw.startswith(b"\xef\xbb\xbf")
        or b"\r" in raw
    ):
        _fail(code + "_FRAMING_INVALID")
    rows = []
    for line_number, line in enumerate(raw[:-1].split(b"\n"), 1):
        if not line:
            _fail(code + f"_EMPTY_LINE:{line_number}")
        try:
            value = parse_json_bytes(line)
        except CanonicalizationError as exc:
            raise GitActiveTreePolicyError(
                code + f"_JSON_INVALID:{line_number}"
            ) from exc
        if not isinstance(value, dict) or canonicalize_object(value) != line:
            _fail(code + f"_JCS_INVALID:{line_number}")
        rows.append(value)
    return tuple(rows)


def _validate_evidence_instance(
    context: GitActiveTreePolicyContext,
    value: Mapping[str, Any],
    schema_id: str,
    expected_bundle_digest: str,
    code: str,
) -> None:
    try:
        validate_instance(
            context.evidence_bundle,
            value,
            schema_id,
            expected_bundle_digest=expected_bundle_digest,
            verify_digest=True,
            public=True,
        )
    except (ContractError, AU040ContractError) as exc:
        raise GitActiveTreePolicyError(code + ":" + str(exc)) from exc


def build_git_active_tree_contract(
    acceptance: AU040AcceptanceContract,
    *,
    observation_schema: Mapping[str, Any],
    expected_observation_schema_digest: str,
    plan_schema: Mapping[str, Any],
    expected_plan_schema_digest: str,
) -> GitActiveTreePolicyContext:
    """Add exact M-063 evidence schemas to the immutable 31/5 contract."""

    if (
        len(acceptance.bundle.schemas) != 31
        or len(acceptance.bundle.policies) != 5
        or DAILY_MANIFEST_SCHEMA_ID not in acceptance.bundle.schemas
        or INDEX_ENTRY_SCHEMA_ID not in acceptance.bundle.schemas
        or RETENTION_RECEIPT_SCHEMA_ID not in acceptance.bundle.schemas
    ):
        _fail("GIT_ACTIVE_TREE_FINAL_31_5_CONTRACT_REQUIRED")
    policy = acceptance.bundle.policies.get(RETENTION_POLICY_ID)
    if (
        not isinstance(policy, dict)
        or canonical_digest(policy) != RETENTION_POLICY_SHA256
        or policy.get("sanitized_public_elapsed_seconds")
        != 365 * 24 * 60 * 60
        or policy.get("boundary_at_retention_not_before_retained")
        is not True
        or policy.get("history_rewrite_allowed") is not False
    ):
        _fail("GIT_ACTIVE_TREE_RETENTION_POLICY_MISMATCH")

    schemas = dict(acceptance.bundle.schemas)
    pointers = dict(acceptance.bundle.self_digest_pointers)
    additions = (
        (
            OBSERVATION_SCHEMA_ID,
            observation_schema,
            expected_observation_schema_digest,
            OBSERVATION_SELF_POINTER,
        ),
        (
            PLAN_SCHEMA_ID,
            plan_schema,
            expected_plan_schema_digest,
            PLAN_SELF_POINTER,
        ),
    )
    for schema_id, document, digest, pointer in additions:
        if (
            not isinstance(document, dict)
            or document.get("$id") != schema_id
            or not isinstance(digest, str)
            or SHA256_RE.fullmatch(digest) is None
            or canonical_digest(document) != digest
        ):
            _fail("GIT_ACTIVE_TREE_EVIDENCE_SCHEMA_TRUST_MISMATCH")
        if schema_id in schemas:
            _fail("GIT_ACTIVE_TREE_EVIDENCE_SCHEMA_REBIND_FORBIDDEN")
        schemas[schema_id] = document
        pointers[schema_id] = pointer
    try:
        registry, format_checker = build_registry(schemas)
    except (ContractError, AU040ContractError) as exc:
        raise GitActiveTreePolicyError(
            "GIT_ACTIVE_TREE_SCHEMA_CLOSURE_INVALID:" + str(exc)
        ) from exc
    return GitActiveTreePolicyContext(
        acceptance=acceptance,
        evidence_bundle=ContractBundle(
            schemas=schemas,
            registry=registry,
            format_checker=format_checker,
            self_digest_pointers=pointers,
            policies=acceptance.bundle.policies,
            protocol_revision=acceptance.bundle.protocol_revision,
        ),
    )


def _manifest_history(
    context: GitActiveTreePolicyContext,
    raw_history: Mapping[str, bytes],
    *,
    expected_bundle_digest: str,
) -> Tuple[Tuple[str, Mapping[str, Any]], ...]:
    if not isinstance(raw_history, dict) or not raw_history:
        _fail("GIT_ACTIVE_TREE_MANIFEST_HISTORY_EMPTY")
    parsed = []
    prefix: Optional[str] = None
    local_date: Optional[str] = None
    for path, raw in raw_history.items():
        match = MANIFEST_PATH_RE.fullmatch(path)
        if match is None:
            _fail("GIT_ACTIVE_TREE_MANIFEST_PATH_INVALID")
        number = int(match.group("number"))
        if number < 1:
            _fail("GIT_ACTIVE_TREE_MANIFEST_REVISION_INVALID")
        observed_date = _date_from_match(
            match,
            "GIT_ACTIVE_TREE_MANIFEST_DATE_INVALID",
        )
        observed_prefix = path.rsplit("/", 1)[0]
        if prefix is None:
            prefix = observed_prefix
            local_date = observed_date
        elif prefix != observed_prefix or local_date != observed_date:
            _fail("GIT_ACTIVE_TREE_MANIFEST_HISTORY_MULTIPLE_DAYS")
        manifest = _parse_object(
            raw,
            maximum_bytes=MAX_OBJECT_BYTES,
            code="GIT_ACTIVE_TREE_MANIFEST",
        )
        if (
            manifest.get("manifest_revision") != number
            or manifest.get("local_date") != observed_date
        ):
            _fail("GIT_ACTIVE_TREE_MANIFEST_PATH_IDENTITY_MISMATCH")
        parsed.append((number, path, manifest))
    parsed.sort(key=lambda row: row[0])
    revisions = [row[0] for row in parsed]
    if revisions != list(range(1, len(parsed) + 1)):
        _fail("GIT_ACTIVE_TREE_MANIFEST_HISTORY_NOT_CONTIGUOUS")
    for index, (_, path, current) in enumerate(parsed):
        prior_path: Optional[str] = None
        prior: Optional[Mapping[str, Any]] = None
        if index:
            prior_path = parsed[index - 1][1]
            prior = parsed[index - 1][2]
        try:
            validate_manifest_revision_chain(
                context.acceptance,
                current,
                path,
                prior,
                prior_path,
                expected_bundle_digest=expected_bundle_digest,
            )
        except (ContractError, AU040ContractError) as exc:
            raise GitActiveTreePolicyError(
                "GIT_ACTIVE_TREE_MANIFEST_HISTORY_INVALID:" + str(exc)
            ) from exc
    return tuple((path, manifest) for _, path, manifest in parsed)


def _artifact_descriptor_map(
    material: Mapping[str, bytes],
    pattern: re.Pattern[str],
    *,
    expected_prefix: str,
    code: str,
) -> Tuple[
    Dict[str, Mapping[str, Any]],
    Dict[str, Tuple[Mapping[str, Any], ...]],
]:
    descriptors: Dict[str, Mapping[str, Any]] = {}
    rows_by_path: Dict[str, Tuple[Mapping[str, Any], ...]] = {}
    for path, raw in material.items():
        match = pattern.fullmatch(path)
        if match is None or path.rsplit("/", 1)[0] != expected_prefix:
            _fail(code + "_PATH_INVALID")
        if int(match.group("number")) < 1:
            _fail(code + "_NUMBER_INVALID")
        rows = _parse_jsonl(raw, code=code)
        descriptors[path] = {
            "digest": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "records": len(rows),
        }
        rows_by_path[path] = rows
    return descriptors, rows_by_path


def _receipt_objects(
    context: GitActiveTreePolicyContext,
    material: Mapping[str, bytes],
    *,
    expected_prefix: str,
    expected_bundle_digest: str,
) -> Mapping[str, Mapping[str, Any]]:
    receipts: Dict[str, Mapping[str, Any]] = {}
    for path, raw in material.items():
        match = RECEIPT_PATH_RE.fullmatch(path)
        if (
            match is None
            or path.rsplit("/", 1)[0] != expected_prefix
            or int(match.group("number")) < 1
        ):
            _fail("GIT_ACTIVE_TREE_RECEIPT_PATH_INVALID")
        receipt = _parse_object(
            raw,
            maximum_bytes=MAX_OBJECT_BYTES,
            code="GIT_ACTIVE_TREE_RECEIPT",
        )
        try:
            validate_retention_receipt_semantics(
                context.acceptance,
                receipt,
                expected_bundle_digest=expected_bundle_digest,
            )
        except (ContractError, AU040ContractError) as exc:
            raise GitActiveTreePolicyError(
                "GIT_ACTIVE_TREE_RECEIPT_INVALID:" + str(exc)
            ) from exc
        receipts[path] = receipt
    return receipts


def _validate_pruned_history_links(
    history: Sequence[Tuple[str, Mapping[str, Any]]],
    receipts: Mapping[str, Mapping[str, Any]],
) -> None:
    latest = history[-1][1]
    required_paths = {
        part["retention_receipt_path"]
        for part in latest["parts"]
        if part["state"] == "PRUNED"
    }
    if set(receipts) != required_paths:
        _fail("GIT_ACTIVE_TREE_RECEIPT_SET_MISMATCH")

    transition_by_part: Dict[
        int,
        Tuple[
            Mapping[str, Any],
            Mapping[str, Any],
            Mapping[str, Any],
        ],
    ] = {}
    for revision in range(1, len(history)):
        prior = history[revision - 1][1]
        current = history[revision][1]
        for old, new in zip(prior["parts"], current["parts"]):
            if old["state"] == "ACTIVE" and new["state"] == "PRUNED":
                transition_by_part[int(new["part_number"])] = (
                    prior,
                    current,
                    new,
                )

    expected_affected: Dict[str, Dict[str, Mapping[str, Any]]] = {}
    prefix = history[-1][0].rsplit("/", 1)[0]
    for part in latest["parts"]:
        if part["state"] != "PRUNED":
            continue
        number = int(part["part_number"])
        transition = transition_by_part.get(number)
        if transition is None:
            _fail("GIT_ACTIVE_TREE_PRUNED_TRANSITION_NOT_FOUND")
        prior_manifest, transition_manifest, transition_part = transition
        receipt_path = transition_part["retention_receipt_path"]
        receipt = receipts.get(receipt_path)
        if receipt is None:
            _fail("GIT_ACTIVE_TREE_PRUNED_RECEIPT_MISSING")
        if (
            receipt.get("receipt_uid")
            != transition_part["retention_receipt_uid"]
            or receipt.get("receipt_digest")
            != transition_part["retention_receipt_digest"]
            or receipt.get("executed_at") != transition_part["pruned_at"]
            or receipt.get("auto_transaction_uid")
            != transition_manifest["auto_transaction_uid"]
        ):
            _fail("GIT_ACTIVE_TREE_PRUNED_RECEIPT_IDENTITY_MISMATCH")
        shard_path = f"{prefix}/part-{number:04d}.jsonl"
        affected = [
            item
            for item in receipt["affected_public_artifacts"]
            if item["artifact_repo_path"] == shard_path
        ]
        if len(affected) != 1:
            _fail("GIT_ACTIVE_TREE_PRUNED_RECEIPT_PART_NOT_EXACT")
        item = affected[0]
        expected = {
            "artifact_schema_id": PUBLIC_RUN_EVENT_SCHEMA_ID,
            "artifact_serialization": JSONL_SERIALIZATION,
            "prior_artifact_digest": transition_part["shard_digest"],
            "prior_artifact_bytes": transition_part["shard_bytes"],
            "prior_record_count": transition_part["record_count"],
            "first_published_at": transition_part["first_published_at"],
            "retention_not_before": transition_part[
                "retention_not_before"
            ],
            "retained_index_path": (
                f"{prefix}/index-{number:04d}.jsonl"
            ),
            "retained_index_digest": transition_part["index_digest"],
            "prior_daily_manifest_digest": prior_manifest[
                "manifest_digest"
            ],
        }
        if any(item.get(key) != value for key, value in expected.items()):
            _fail("GIT_ACTIVE_TREE_PRUNED_RECEIPT_PART_MISMATCH")
        expected_affected.setdefault(receipt_path, {})[shard_path] = item

    for receipt_path, receipt in receipts.items():
        observed = {
            item["artifact_repo_path"]: item
            for item in receipt["affected_public_artifacts"]
        }
        if observed != expected_affected.get(receipt_path, {}):
            _fail("GIT_ACTIVE_TREE_RECEIPT_AFFECTED_SET_MISMATCH")


def validate_daily_tree_material(
    context: GitActiveTreePolicyContext,
    *,
    manifest_history_bytes: Mapping[str, bytes],
    part_bytes: Mapping[str, bytes],
    index_bytes: Mapping[str, bytes],
    receipt_bytes: Mapping[str, bytes],
    expected_bundle_digest: str,
) -> DailyTreeMaterial:
    """Validate the complete latest current-tree material for one day."""

    history = _manifest_history(
        context,
        manifest_history_bytes,
        expected_bundle_digest=expected_bundle_digest,
    )
    latest_path, latest = history[-1]
    prefix = latest_path.rsplit("/", 1)[0]
    part_descriptors, part_rows = _artifact_descriptor_map(
        part_bytes,
        PART_PATH_RE,
        expected_prefix=prefix,
        code="GIT_ACTIVE_TREE_PART",
    )
    index_descriptors, index_rows = _artifact_descriptor_map(
        index_bytes,
        INDEX_PATH_RE,
        expected_prefix=prefix,
        code="GIT_ACTIVE_TREE_INDEX",
    )
    receipts = _receipt_objects(
        context,
        receipt_bytes,
        expected_prefix=prefix,
        expected_bundle_digest=expected_bundle_digest,
    )
    _validate_pruned_history_links(history, receipts)

    descriptors = dict(part_descriptors)
    descriptors.update(index_descriptors)
    expected_paths = set()
    known_events: Dict[str, str] = {}
    for part in latest["parts"]:
        number = int(part["part_number"])
        shard_path = f"{prefix}/part-{number:04d}.jsonl"
        index_path = f"{prefix}/index-{number:04d}.jsonl"
        expected_paths.add(index_path)
        if index_path not in index_bytes:
            _fail("GIT_ACTIVE_TREE_RETAINED_INDEX_MISSING")
        try:
            if part["state"] == "ACTIVE":
                expected_paths.add(shard_path)
                if shard_path not in part_bytes:
                    _fail("GIT_ACTIVE_TREE_ACTIVE_SHARD_MISSING")
                validate_part_index_manifest_closure(
                    context.acceptance,
                    latest,
                    part_number=number,
                    part_bytes=part_bytes[shard_path],
                    index_bytes=index_bytes[index_path],
                    known_events=known_events,
                    expected_bundle_digest=expected_bundle_digest,
                )
            else:
                if shard_path in part_bytes:
                    _fail("GIT_ACTIVE_TREE_PRUNED_SHARD_PRESENT")
                validate_retained_index_manifest_closure(
                    context.acceptance,
                    latest,
                    part_number=number,
                    index_bytes=index_bytes[index_path],
                    known_events=known_events,
                    expected_bundle_digest=expected_bundle_digest,
                )
        except (ContractError, AU040ContractError) as exc:
            raise GitActiveTreePolicyError(
                "GIT_ACTIVE_TREE_PART_INDEX_CLOSURE_INVALID:" + str(exc)
            ) from exc
        for row in index_rows[index_path]:
            uid = str(row["event_uid"])
            digest = str(row["event_digest"])
            if uid in known_events:
                _fail("GIT_ACTIVE_TREE_INDEX_EVENT_UID_DUPLICATE")
            known_events[uid] = digest
    if set(descriptors) != expected_paths:
        _fail("GIT_ACTIVE_TREE_UNLISTED_PART_OR_INDEX")
    if set(part_rows) != set(part_bytes):
        _fail("GIT_ACTIVE_TREE_PART_DESCRIPTOR_SET_MISMATCH")
    return DailyTreeMaterial(
        manifest_history=history,
        latest_manifest_path=latest_path,
        latest_manifest=latest,
        part_bytes=dict(part_bytes),
        index_bytes=dict(index_bytes),
        receipts=receipts,
    )


def _retention_state(
    *,
    state: str,
    observed: dt.datetime,
    anchor: dt.datetime,
) -> str:
    if state == "PRUNED":
        return "ALREADY_PRUNED"
    if observed < anchor:
        return "RETAIN_BEFORE_BOUNDARY"
    if observed == anchor:
        return "RETAIN_AT_BOUNDARY"
    return "ELIGIBLE_AFTER_BOUNDARY"


def validate_retention_observation(
    context: GitActiveTreePolicyContext,
    observation: Mapping[str, Any],
    *,
    expected_bundle_digest: str,
) -> Mapping[str, Any]:
    """Validate one M-063 observation including arithmetic semantics."""

    if not isinstance(observation, dict):
        _fail("GIT_ACTIVE_TREE_OBSERVATION_ROOT_INVALID")
    _validate_evidence_instance(
        context,
        observation,
        OBSERVATION_SCHEMA_ID,
        expected_bundle_digest,
        "GIT_ACTIVE_TREE_OBSERVATION_INVALID",
    )
    observed = _strict_utc(
        observation["observed_at"],
        "GIT_ACTIVE_TREE_OBSERVED_AT_INVALID",
    )
    parts = observation["part_observations"]
    numbers = [part["part_number"] for part in parts]
    if numbers != list(range(1, len(parts) + 1)):
        _fail("GIT_ACTIVE_TREE_OBSERVATION_PART_ORDER_INVALID")
    keep = []
    eligible = []
    pruned = []
    active_bytes = 0
    index_bytes = 0
    for part in parts:
        first = _strict_utc(
            part["first_published_at"],
            "GIT_ACTIVE_TREE_FIRST_PUBLISHED_AT_INVALID",
        )
        anchor = _strict_utc(
            part["retention_not_before"],
            "GIT_ACTIVE_TREE_RETENTION_NOT_BEFORE_INVALID",
        )
        if anchor != first + RETENTION_ELAPSED or observed < first:
            _fail("GIT_ACTIVE_TREE_OBSERVATION_RETENTION_CLOCK_INVALID")
        expected_elapsed = _elapsed_microseconds(observed - first)
        expected_state = _retention_state(
            state=part["state"],
            observed=observed,
            anchor=anchor,
        )
        if (
            part["elapsed_microseconds"] != expected_elapsed
            or part["retention_state"] != expected_state
            or part["retained_index_present"] is not True
        ):
            _fail("GIT_ACTIVE_TREE_OBSERVATION_PART_SEMANTIC_MISMATCH")
        index_bytes += part["index_bytes"]
        if part["state"] == "ACTIVE":
            if (
                part["active_shard_present"] is not True
                or part["full_fidelity_verified"] is not True
            ):
                _fail("GIT_ACTIVE_TREE_ACTIVE_PART_EVIDENCE_INVALID")
            active_bytes += part["shard_bytes"]
            if expected_state == "ELIGIBLE_AFTER_BOUNDARY":
                eligible.append(part)
            else:
                keep.append(part)
        else:
            if (
                part["active_shard_present"] is not False
                or part["full_fidelity_verified"] is not False
                or observed
                < _strict_utc(
                    part["pruned_at"],
                    "GIT_ACTIVE_TREE_PRUNED_AT_INVALID",
                )
            ):
                _fail("GIT_ACTIVE_TREE_PRUNED_PART_EVIDENCE_INVALID")
            pruned.append(part)
    if (
        observation["active_part_count"] != len(keep) + len(eligible)
        or observation["keep_part_count"] != len(keep)
        or observation["eligible_part_count"] != len(eligible)
        or observation["pruned_part_count"] != len(pruned)
        or observation["active_shard_bytes"] != active_bytes
        or observation["retained_index_bytes"] != index_bytes
        or observation["policy_snapshot_digest"]
        != RETENTION_POLICY_SHA256
        or observation["full_fidelity_aggregation_substitution_performed"]
        is not False
        or observation["history_rewrite_performed"] is not False
        or observation["hard_delete_claimed"] is not False
        or observation["state_mutation_performed"] is not False
    ):
        _fail("GIT_ACTIVE_TREE_OBSERVATION_AGGREGATE_MISMATCH")
    return observation


def validate_prune_plan(
    context: GitActiveTreePolicyContext,
    plan: Mapping[str, Any],
    observation: Mapping[str, Any],
    *,
    expected_bundle_digest: str,
) -> Mapping[str, Any]:
    """Validate exact eligible-set projection and non-authority semantics."""

    validate_retention_observation(
        context,
        observation,
        expected_bundle_digest=expected_bundle_digest,
    )
    if not isinstance(plan, dict):
        _fail("GIT_ACTIVE_TREE_PLAN_ROOT_INVALID")
    _validate_evidence_instance(
        context,
        plan,
        PLAN_SCHEMA_ID,
        expected_bundle_digest,
        "GIT_ACTIVE_TREE_PLAN_INVALID",
    )
    if (
        plan["observation_ref"]["observation_uid"]
        != observation["observation_uid"]
        or plan["observation_ref"]["evidence_bundle_digest"]
        != observation["evidence_bundle_digest"]
        or plan["generated_at"] != observation["observed_at"]
        or plan["source_manifest_ref"] != observation["source_manifest"]
    ):
        _fail("GIT_ACTIVE_TREE_PLAN_OBSERVATION_BINDING_MISMATCH")
    observed_eligible = [
        part
        for part in observation["part_observations"]
        if part["retention_state"] == "ELIGIBLE_AFTER_BOUNDARY"
    ]
    expected_candidates = []
    for part in observed_eligible:
        anchor = _strict_utc(
            part["retention_not_before"],
            "GIT_ACTIVE_TREE_PLAN_ANCHOR_INVALID",
        )
        deadline = anchor + PRUNE_DEADLINE
        observed = _strict_utc(
            observation["observed_at"],
            "GIT_ACTIVE_TREE_PLAN_TIME_INVALID",
        )
        breached = observed > deadline
        expected_candidates.append(
            {
                "part_number": part["part_number"],
                "artifact_repo_path": part["shard_path"],
                "prior_artifact_digest": part["shard_digest"],
                "prior_artifact_bytes": part["shard_bytes"],
                "prior_record_count": part["record_count"],
                "first_published_at": part["first_published_at"],
                "retention_not_before": part["retention_not_before"],
                "prune_deadline_at": _format_utc(deadline),
                "retained_index_path": part["index_path"],
                "retained_index_digest": part["index_digest"],
                "prior_daily_manifest_digest": observation[
                    "source_manifest"
                ]["manifest_digest"],
                "deadline_status": (
                    "DEADLINE_BREACHED"
                    if breached
                    else "ON_TIME_WINDOW"
                ),
                "required_gap_code": (
                    "GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH"
                    if breached
                    else None
                ),
            }
        )
    if plan["candidates"] != expected_candidates:
        _fail("GIT_ACTIVE_TREE_PLAN_CANDIDATE_SET_MISMATCH")
    if expected_candidates:
        if (
            plan["decision"] != "PLAN_CURRENT_TREE_PRUNE"
            or plan["action_order"] != list(PRUNE_ACTION_ORDER)
        ):
            _fail("GIT_ACTIVE_TREE_PRUNE_PLAN_DECISION_INVALID")
    elif (
        plan["decision"] != "KEEP_ACTIVE_TREE"
        or plan["action_order"] != list(KEEP_ACTION_ORDER)
    ):
        _fail("GIT_ACTIVE_TREE_KEEP_PLAN_DECISION_INVALID")
    if (
        plan["selected_count"] != len(expected_candidates)
        or plan["selected_bytes"]
        != sum(item["prior_artifact_bytes"] for item in expected_candidates)
        or plan["current_tree_prune_only"] is not True
        or plan["retained_index_required"] is not True
        or plan["full_fidelity_aggregation_substitution_permitted"]
        is not False
        or plan["history_rewrite_performed"] is not False
        or plan["hard_delete_claimed"] is not False
        or plan["delete_authority_granted"] is not False
        or plan["real_execution_permitted"] is not False
        or plan["auto_executor_integration_status"] != "NOT_BOUND"
        or plan["state_mutation_performed"] is not False
    ):
        _fail("GIT_ACTIVE_TREE_PLAN_AUTHORITY_OR_AGGREGATE_MISMATCH")
    return plan


def evaluate_git_active_tree(
    context: GitActiveTreePolicyContext,
    *,
    manifest_history_bytes: Mapping[str, bytes],
    part_bytes: Mapping[str, bytes],
    index_bytes: Mapping[str, bytes],
    receipt_bytes: Mapping[str, bytes],
    observation_uid: str,
    plan_uid: str,
    observed_at: str,
    expected_bundle_digest: str,
) -> GitActiveTreePolicyResult:
    """Validate one daily tree and emit a non-mutating retention plan."""

    material = validate_daily_tree_material(
        context,
        manifest_history_bytes=manifest_history_bytes,
        part_bytes=part_bytes,
        index_bytes=index_bytes,
        receipt_bytes=receipt_bytes,
        expected_bundle_digest=expected_bundle_digest,
    )
    observed = _strict_utc(
        observed_at,
        "GIT_ACTIVE_TREE_OBSERVED_AT_INVALID",
    )
    latest = material.latest_manifest
    prefix = material.latest_manifest_path.rsplit("/", 1)[0]
    part_observations = []
    keep = []
    eligible = []
    pruned = []
    for part in latest["parts"]:
        number = int(part["part_number"])
        first = _strict_utc(
            part["first_published_at"],
            "GIT_ACTIVE_TREE_FIRST_PUBLISHED_AT_INVALID",
        )
        if observed < first:
            _fail("GIT_ACTIVE_TREE_OBSERVED_BEFORE_FIRST_PUBLICATION")
        anchor = _strict_utc(
            part["retention_not_before"],
            "GIT_ACTIVE_TREE_RETENTION_NOT_BEFORE_INVALID",
        )
        state = _retention_state(
            state=str(part["state"]),
            observed=observed,
            anchor=anchor,
        )
        row: Dict[str, Any] = {
            "part_number": number,
            "state": part["state"],
            "shard_path": f"{prefix}/part-{number:04d}.jsonl",
            "index_path": f"{prefix}/index-{number:04d}.jsonl",
            "shard_digest": part["shard_digest"],
            "shard_bytes": part["shard_bytes"],
            "record_count": part["record_count"],
            "index_digest": part["index_digest"],
            "index_bytes": part["index_bytes"],
            "index_record_count": part["index_record_count"],
            "first_published_at": part["first_published_at"],
            "retention_not_before": part["retention_not_before"],
            "elapsed_microseconds": _elapsed_microseconds(
                observed - first
            ),
            "retention_state": state,
            "active_shard_present": part["state"] == "ACTIVE",
            "retained_index_present": True,
            "full_fidelity_verified": part["state"] == "ACTIVE",
        }
        if part["state"] == "PRUNED":
            row["pruned_at"] = part["pruned_at"]
            pruned.append(number)
        elif state == "ELIGIBLE_AFTER_BOUNDARY":
            eligible.append(number)
        else:
            keep.append(number)
        part_observations.append(row)
    observation: Dict[str, Any] = {
        "schema_version": OBSERVATION_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": expected_bundle_digest,
        "observation_uid": observation_uid,
        "observed_at": observed_at,
        "scope": "GIT_CURRENT_TREE",
        "clock_basis": "UTC_WALL_CLOCK",
        "retention_policy_id": RETENTION_POLICY_ID,
        "policy_snapshot_digest": RETENTION_POLICY_SHA256,
        "source_manifest": {
            "artifact_repo_path": material.latest_manifest_path,
            "manifest_uid": latest["manifest_uid"],
            "manifest_digest": latest["manifest_digest"],
            "manifest_revision": latest["manifest_revision"],
            "local_date": latest["local_date"],
            "previous_manifest_digest": latest[
                "previous_manifest_digest"
            ],
        },
        "manifest_history_count": len(material.manifest_history),
        "part_observations": part_observations,
        "active_part_count": latest["active_part_count"],
        "keep_part_count": len(keep),
        "eligible_part_count": len(eligible),
        "pruned_part_count": latest["pruned_part_count"],
        "active_shard_bytes": latest["active_shard_bytes"],
        "retained_index_bytes": latest["retained_index_bytes"],
        "full_fidelity_aggregation_substitution_performed": False,
        "history_rewrite_performed": False,
        "hard_delete_claimed": False,
        "state_mutation_performed": False,
        "evidence_bundle_digest": "0" * 64,
    }
    observation["evidence_bundle_digest"] = canonical_digest(
        observation,
        OBSERVATION_SELF_POINTER,
    )
    validate_retention_observation(
        context,
        observation,
        expected_bundle_digest=expected_bundle_digest,
    )

    candidates = []
    for row in part_observations:
        if row["retention_state"] != "ELIGIBLE_AFTER_BOUNDARY":
            continue
        anchor = _strict_utc(
            row["retention_not_before"],
            "GIT_ACTIVE_TREE_PLAN_ANCHOR_INVALID",
        )
        deadline = anchor + PRUNE_DEADLINE
        breached = observed > deadline
        candidates.append(
            {
                "part_number": row["part_number"],
                "artifact_repo_path": row["shard_path"],
                "prior_artifact_digest": row["shard_digest"],
                "prior_artifact_bytes": row["shard_bytes"],
                "prior_record_count": row["record_count"],
                "first_published_at": row["first_published_at"],
                "retention_not_before": row["retention_not_before"],
                "prune_deadline_at": _format_utc(deadline),
                "retained_index_path": row["index_path"],
                "retained_index_digest": row["index_digest"],
                "prior_daily_manifest_digest": latest[
                    "manifest_digest"
                ],
                "deadline_status": (
                    "DEADLINE_BREACHED"
                    if breached
                    else "ON_TIME_WINDOW"
                ),
                "required_gap_code": (
                    "GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH"
                    if breached
                    else None
                ),
            }
        )
    plan: Dict[str, Any] = {
        "schema_version": PLAN_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": expected_bundle_digest,
        "plan_uid": plan_uid,
        "generated_at": observed_at,
        "observation_ref": {
            "observation_uid": observation_uid,
            "evidence_bundle_digest": observation[
                "evidence_bundle_digest"
            ],
        },
        "source_manifest_ref": observation["source_manifest"],
        "decision": (
            "PLAN_CURRENT_TREE_PRUNE"
            if candidates
            else "KEEP_ACTIVE_TREE"
        ),
        "selected_count": len(candidates),
        "selected_bytes": sum(
            item["prior_artifact_bytes"] for item in candidates
        ),
        "candidates": candidates,
        "action_order": list(
            PRUNE_ACTION_ORDER if candidates else KEEP_ACTION_ORDER
        ),
        "current_tree_prune_only": True,
        "retained_index_required": True,
        "full_fidelity_aggregation_substitution_permitted": False,
        "history_rewrite_performed": False,
        "hard_delete_claimed": False,
        "delete_authority_granted": False,
        "real_execution_permitted": False,
        "auto_executor_integration_status": "NOT_BOUND",
        "state_mutation_performed": False,
        "evidence_bundle_digest": "0" * 64,
    }
    plan["evidence_bundle_digest"] = canonical_digest(
        plan,
        PLAN_SELF_POINTER,
    )
    validate_prune_plan(
        context,
        plan,
        observation,
        expected_bundle_digest=expected_bundle_digest,
    )
    return GitActiveTreePolicyResult(
        canonical_observation_bytes=canonicalize_object(observation),
        observation_digest=observation["evidence_bundle_digest"],
        canonical_plan_bytes=canonicalize_object(plan),
        plan_digest=plan["evidence_bundle_digest"],
        keep_part_numbers=tuple(keep),
        eligible_part_numbers=tuple(eligible),
        already_pruned_part_numbers=tuple(pruned),
    )


def validate_prune_transition(
    context: GitActiveTreePolicyContext,
    *,
    manifest_history_bytes: Mapping[str, bytes],
    current_part_bytes: Mapping[str, bytes],
    current_index_bytes: Mapping[str, bytes],
    current_receipt_bytes: Mapping[str, bytes],
    deleted_prior_part_bytes: Mapping[str, bytes],
    publication: Mapping[str, Any],
    expected_bundle_digest: str,
) -> Mapping[str, Any]:
    """Validate an exact planned prune transaction without executing it."""

    material = validate_daily_tree_material(
        context,
        manifest_history_bytes=manifest_history_bytes,
        part_bytes=current_part_bytes,
        index_bytes=current_index_bytes,
        receipt_bytes=current_receipt_bytes,
        expected_bundle_digest=expected_bundle_digest,
    )
    if len(material.manifest_history) < 2:
        _fail("GIT_ACTIVE_TREE_PRUNE_PREDECESSOR_REQUIRED")
    prior_path, prior = material.manifest_history[-2]
    current_path, current = material.manifest_history[-1]
    newly_pruned = []
    for old, new in zip(prior["parts"], current["parts"]):
        if old["state"] == "ACTIVE" and new["state"] == "PRUNED":
            newly_pruned.append(int(new["part_number"]))
    if not newly_pruned:
        _fail("GIT_ACTIVE_TREE_PRUNE_TRANSITION_EMPTY")
    prefix = current_path.rsplit("/", 1)[0]
    expected_deleted = {
        f"{prefix}/part-{number:04d}.jsonl"
        for number in newly_pruned
    }
    if set(deleted_prior_part_bytes) != expected_deleted:
        _fail("GIT_ACTIVE_TREE_DELETED_PRIOR_PART_SET_MISMATCH")
    for number in newly_pruned:
        shard_path = f"{prefix}/part-{number:04d}.jsonl"
        index_path = f"{prefix}/index-{number:04d}.jsonl"
        try:
            validate_part_index_manifest_closure(
                context.acceptance,
                prior,
                part_number=number,
                part_bytes=deleted_prior_part_bytes[shard_path],
                index_bytes=current_index_bytes[index_path],
                expected_bundle_digest=expected_bundle_digest,
            )
        except (ContractError, AU040ContractError) as exc:
            raise GitActiveTreePolicyError(
                "GIT_ACTIVE_TREE_PRIOR_DELETE_BYTES_INVALID:" + str(exc)
            ) from exc

    transition_receipt_paths = {
        current["parts"][number - 1]["retention_receipt_path"]
        for number in newly_pruned
    }
    transaction_receipts = {
        path: material.receipts[path]
        for path in transition_receipt_paths
    }
    try:
        validate_publication_artifact_set(
            context.acceptance,
            publication,
            expected_bundle_digest=expected_bundle_digest,
        )
        validate_prune_transaction_closure(
            context.acceptance,
            publication,
            current,
            current_path,
            transaction_receipts,
            expected_bundle_digest=expected_bundle_digest,
        )
    except (ContractError, AU040ContractError) as exc:
        raise GitActiveTreePolicyError(
            "GIT_ACTIVE_TREE_PRUNE_TRANSACTION_INVALID:" + str(exc)
        ) from exc

    run_log_paths = set()
    for lane in publication["lane_manifests"]:
        if lane["lane"] != "RUN_LOG":
            continue
        for artifact in lane["artifacts"]:
            path = artifact["artifact_repo_path"]
            if path.startswith(prefix + "/"):
                run_log_paths.add(path)
    appended = range(len(prior["parts"]) + 1, len(current["parts"]) + 1)
    expected_paths = {current_path, *expected_deleted, *transition_receipt_paths}
    for number in appended:
        expected_paths.add(f"{prefix}/part-{number:04d}.jsonl")
        expected_paths.add(f"{prefix}/index-{number:04d}.jsonl")
    if run_log_paths != expected_paths:
        _fail("GIT_ACTIVE_TREE_PRUNE_TRANSACTION_PATH_SET_MISMATCH")
    if current["previous_manifest_digest"] != prior["manifest_digest"]:
        _fail("GIT_ACTIVE_TREE_PRUNE_PREDECESSOR_DIGEST_MISMATCH")
    return {
        "current_manifest_path": current_path,
        "current_manifest_digest": current["manifest_digest"],
        "prior_manifest_path": prior_path,
        "prior_manifest_digest": prior["manifest_digest"],
        "deleted_part_numbers": tuple(newly_pruned),
        "retained_index_count": len(current["parts"]),
        "transaction_receipt_paths": tuple(
            sorted(transition_receipt_paths)
        ),
        "history_rewrite_performed": False,
        "hard_delete_claimed": False,
        "real_execution_performed": False,
    }
