"""Deterministic AU-040 shard/index/daily-manifest byte planner.

This module never writes the repository and does not invoke the publisher.
It validates an existing canonical daily tree through descriptor-relative
``O_NOFOLLOW`` reads and returns exact in-memory PUT artifacts for a later,
separately authorized publication-manifest:v2 integration.
"""

from __future__ import annotations

import copy
import datetime as dt
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

from CodexSkills.governance.tools.canonical_json import (
    canonicalize_object,
    parse_json_bytes,
)
from CodexSkills.registry.auto.tools.validate_auto import (
    AutoContract,
    validate_auto_instance,
)

from .core import (
    AutoRuntimeError,
    PROTOCOL,
    SCHEMA_PREFIX,
    canonical_with_digest,
    format_utc,
    parse_utc,
    sha256_bytes,
)
from .privacy import validate_public_serialization


DAILY_MANIFEST_SCHEMA = (
    SCHEMA_PREFIX + "daily-run-shard-manifest:v1"
)
INDEX_ENTRY_SCHEMA = SCHEMA_PREFIX + "run-event-index-entry:v1"
PUBLIC_RUN_EVENT_SCHEMA = SCHEMA_PREFIX + "public-run-event:v2"
RETENTION_RECEIPT_SCHEMA = SCHEMA_PREFIX + "retention-receipt:v3"
JSONL_SERIALIZATION = "RFC8785_JCS_PER_LINE_LF"
OBJECT_SERIALIZATION = "RFC8785_JCS_OBJECT"
RUN_LOG_ROOT = "OpenAIDatabase/data/run_logs/skills_runs"
MAX_PART_BYTES = 20 * 1024 * 1024
MAX_SEQUENCE = 9999
MAX_DAILY_ENTRIES = 10_000
RETENTION_AGE = dt.timedelta(days=365)
SYDNEY = ZoneInfo("Australia/Sydney")
MANIFEST_NAME_RE = re.compile(r"^manifest-([0-9]{4})\.json$")
INDEX_NAME_RE = re.compile(r"^index-([0-9]{4})\.jsonl$")
PART_NAME_RE = re.compile(r"^part-([0-9]{4})\.jsonl$")
RETENTION_NAME_RE = re.compile(
    r"^retention-receipt-([0-9]{4})\.json$"
)


@dataclass(frozen=True)
class RunLogArtifact:
    relative_path: str
    schema_id: str
    serialization: str
    payload: bytes
    record_count: int


@dataclass(frozen=True)
class ExistingDailyTree:
    local_date: str
    manifest_path: str
    manifest_raw: bytes
    manifest: Mapping[str, Any]
    index_entries: Tuple[Mapping[str, Any], ...]
    event_digests: Mapping[str, str]
    last_event_key: Tuple[dt.datetime, str]


@dataclass(frozen=True)
class RunLogWritePlan:
    local_date: str
    manifest_revision: int
    previous_manifest_digest: Optional[str]
    manifest: Mapping[str, Any]
    artifacts: Tuple[RunLogArtifact, ...]
    input_event_count: int
    deduplicated_event_count: int
    new_event_count: int


def _canonical_date(value: str) -> dt.date:
    try:
        parsed = dt.date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise AutoRuntimeError("RUN_LOG_LOCAL_DATE_INVALID") from exc
    if parsed.isoformat() != value:
        raise AutoRuntimeError("RUN_LOG_LOCAL_DATE_NONCANONICAL")
    return parsed


def _event_key(event: Mapping[str, Any]) -> Tuple[dt.datetime, str]:
    return (parse_utc(str(event["occurred_at"])), str(event["event_uid"]))


def _sydney_date(timestamp: str) -> str:
    return parse_utc(timestamp).astimezone(SYDNEY).date().isoformat()


def _read_regular_at(
    directory_fd: int,
    name: str,
    *,
    maximum_bytes: int,
) -> bytes:
    try:
        before = os.stat(
            name,
            dir_fd=directory_fd,
            follow_symlinks=False,
        )
    except OSError as exc:
        raise AutoRuntimeError("RUN_LOG_TREE_FILE_STAT_FAILED") from exc
    if not stat.S_ISREG(before.st_mode):
        raise AutoRuntimeError("RUN_LOG_TREE_FILE_NOT_REGULAR")
    descriptor: Optional[int] = None
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=directory_fd,
        )
        after = os.fstat(descriptor)
        if (
            not stat.S_ISREG(after.st_mode)
            or (before.st_dev, before.st_ino)
            != (after.st_dev, after.st_ino)
        ):
            raise AutoRuntimeError("RUN_LOG_TREE_FILE_REBOUND")
        chunks = []
        observed = 0
        while True:
            block = os.read(
                descriptor,
                min(1024 * 1024, maximum_bytes + 1 - observed),
            )
            if not block:
                break
            chunks.append(block)
            observed += len(block)
            if observed > maximum_bytes:
                raise AutoRuntimeError("RUN_LOG_TREE_FILE_TOO_LARGE")
        return b"".join(chunks)
    except AutoRuntimeError:
        raise
    except OSError as exc:
        raise AutoRuntimeError("RUN_LOG_TREE_FILE_READ_FAILED") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _open_real_directory(path: Path) -> int:
    try:
        info = os.lstat(str(path))
    except OSError as exc:
        raise AutoRuntimeError("RUN_LOG_TREE_ROOT_STAT_FAILED") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise AutoRuntimeError("RUN_LOG_TREE_ROOT_NOT_REAL_DIRECTORY")
    try:
        return os.open(
            str(path),
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as exc:
        raise AutoRuntimeError("RUN_LOG_TREE_ROOT_OPEN_FAILED") from exc


def _open_directory_at(parent_fd: int, name: str) -> int:
    try:
        before = os.stat(
            name,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
    except OSError as exc:
        raise AutoRuntimeError("RUN_LOG_TREE_PARENT_STAT_FAILED") from exc
    if not stat.S_ISDIR(before.st_mode):
        raise AutoRuntimeError("RUN_LOG_TREE_PARENT_NOT_REAL_DIRECTORY")
    descriptor: Optional[int] = None
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
        after = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(after.st_mode)
            or (before.st_dev, before.st_ino)
            != (after.st_dev, after.st_ino)
        ):
            raise AutoRuntimeError("RUN_LOG_TREE_PARENT_REBOUND")
        return descriptor
    except AutoRuntimeError:
        if descriptor is not None:
            os.close(descriptor)
        raise
    except OSError as exc:
        if descriptor is not None:
            os.close(descriptor)
        raise AutoRuntimeError("RUN_LOG_TREE_PARENT_OPEN_FAILED") from exc


def _validate_jsonl(
    raw: bytes,
    *,
    contract: AutoContract,
    schema_id: str,
    bundle_digest: str,
) -> Tuple[Mapping[str, Any], ...]:
    if (
        not raw
        or len(raw) > MAX_PART_BYTES
        or not raw.endswith(b"\n")
        or b"\r" in raw
        or raw.startswith(b"\xef\xbb\xbf")
    ):
        raise AutoRuntimeError("RUN_LOG_JSONL_FRAMING_INVALID")
    rows = []
    for line_number, line in enumerate(raw[:-1].split(b"\n"), 1):
        if not line:
            raise AutoRuntimeError(
                f"RUN_LOG_JSONL_EMPTY_LINE:{line_number}"
            )
        try:
            parsed = parse_json_bytes(line)
            canonical = canonicalize_object(parsed)
        except Exception as exc:
            raise AutoRuntimeError(
                f"RUN_LOG_JSONL_LINE_INVALID:{line_number}"
            ) from exc
        if not isinstance(parsed, dict) or canonical != line:
            raise AutoRuntimeError(
                f"RUN_LOG_JSONL_LINE_NOT_JCS:{line_number}"
            )
        validate_public_serialization(
            line,
            contract,
            schema_id,
            bundle_digest,
        )
        rows.append(MappingProxyType(parsed))
    return tuple(rows)


class DailyRunTreeReader:
    """Read and prove one existing daily tree without following links."""

    def __init__(
        self,
        repo_root: Path,
        contract: AutoContract,
        bundle_digest: str,
    ) -> None:
        self.repo_root = repo_root
        self.contract = contract
        self.bundle_digest = bundle_digest

    def load(self, local_date: str) -> ExistingDailyTree:
        date = _canonical_date(local_date)
        descriptors = []
        root_fd = _open_real_directory(self.repo_root)
        descriptors.append(root_fd)
        current_fd = root_fd
        try:
            for part in (
                "OpenAIDatabase",
                "data",
                "run_logs",
                "skills_runs",
                f"{date.year:04d}",
                f"{date.month:02d}",
                f"{date.day:02d}",
            ):
                current_fd = _open_directory_at(current_fd, part)
                descriptors.append(current_fd)
            names = sorted(os.listdir(current_fd))
            if len(names) > MAX_DAILY_ENTRIES:
                raise AutoRuntimeError(
                    "RUN_LOG_TREE_ENTRY_BUDGET_EXCEEDED"
                )
            if any(
                not (
                    MANIFEST_NAME_RE.fullmatch(name)
                    or INDEX_NAME_RE.fullmatch(name)
                    or PART_NAME_RE.fullmatch(name)
                    or RETENTION_NAME_RE.fullmatch(name)
                )
                for name in names
            ):
                raise AutoRuntimeError("RUN_LOG_TREE_UNLISTED_ENTRY")

            manifest_names = [
                name for name in names if MANIFEST_NAME_RE.fullmatch(name)
            ]
            revisions = [
                int(MANIFEST_NAME_RE.fullmatch(name).group(1))
                for name in manifest_names
            ]
            if (
                not revisions
                or revisions != list(range(1, len(revisions) + 1))
                or revisions[-1] > MAX_SEQUENCE
            ):
                raise AutoRuntimeError(
                    "RUN_LOG_MANIFEST_REVISIONS_NOT_GAPLESS"
                )

            manifests = []
            previous_digest: Optional[str] = None
            for revision, name in zip(revisions, manifest_names):
                raw = _read_regular_at(
                    current_fd,
                    name,
                    maximum_bytes=MAX_PART_BYTES,
                )
                try:
                    parsed = parse_json_bytes(raw)
                except Exception as exc:
                    raise AutoRuntimeError(
                        "RUN_LOG_MANIFEST_JSON_INVALID"
                    ) from exc
                if (
                    not isinstance(parsed, dict)
                    or canonicalize_object(parsed) != raw
                ):
                    raise AutoRuntimeError(
                        "RUN_LOG_MANIFEST_NOT_EXACT_JCS"
                    )
                validate_public_serialization(
                    raw,
                    self.contract,
                    DAILY_MANIFEST_SCHEMA,
                    self.bundle_digest,
                )
                if (
                    parsed["manifest_revision"] != revision
                    or parsed["local_date"] != local_date
                    or parsed["previous_manifest_digest"]
                    != previous_digest
                ):
                    raise AutoRuntimeError(
                        "RUN_LOG_MANIFEST_PREDECESSOR_CHAIN_INVALID"
                    )
                previous_digest = parsed["manifest_digest"]
                manifests.append((name, raw, parsed))

            prune_prior_digests: Dict[int, str] = {}
            if any(
                part["state"] == "PRUNED"
                for part in manifests[0][2]["parts"]
            ):
                raise AutoRuntimeError(
                    "RUN_LOG_MANIFEST_REVISION_ONE_PRUNED"
                )
            for (_, _, before), (_, _, after) in zip(
                manifests,
                manifests[1:],
            ):
                before_parts = before["parts"]
                after_parts = after["parts"]
                if len(after_parts) < len(before_parts):
                    raise AutoRuntimeError(
                        "RUN_LOG_MANIFEST_PART_REMOVED"
                    )
                for old, new in zip(before_parts, after_parts):
                    if new == old:
                        continue
                    restored = copy.deepcopy(new)
                    if (
                        old["state"] != "ACTIVE"
                        or new["state"] != "PRUNED"
                    ):
                        raise AutoRuntimeError(
                            "RUN_LOG_MANIFEST_PART_MUTATED"
                        )
                    restored["state"] = "ACTIVE"
                    for field in (
                        "retention_receipt_path",
                        "retention_receipt_uid",
                        "retention_receipt_digest",
                        "pruned_at",
                    ):
                        restored.pop(field, None)
                    if restored != old:
                        raise AutoRuntimeError(
                            "RUN_LOG_MANIFEST_PART_MUTATED"
                        )
                    prune_prior_digests[new["part_number"]] = before[
                        "manifest_digest"
                    ]
                if any(
                    part["state"] != "ACTIVE"
                    for part in after_parts[len(before_parts) :]
                ):
                    raise AutoRuntimeError(
                        "RUN_LOG_MANIFEST_NEW_PART_NOT_ACTIVE"
                    )

            latest_name, latest_raw, latest = manifests[-1]
            expected_names = set(manifest_names)
            all_entries = []
            known: Dict[str, str] = {}
            last_key: Optional[Tuple[dt.datetime, str]] = None
            prefix = (
                f"{RUN_LOG_ROOT}/{date.year:04d}/"
                f"{date.month:02d}/{date.day:02d}"
            )
            receipts: Dict[str, Mapping[str, Any]] = {}
            for part in latest["parts"]:
                number = part["part_number"]
                index_name = f"index-{number:04d}.jsonl"
                part_name = f"part-{number:04d}.jsonl"
                if (
                    part["index_name"] != index_name
                    or part["shard_name"] != part_name
                ):
                    raise AutoRuntimeError(
                        "RUN_LOG_MANIFEST_PART_NAME_INVALID"
                    )
                expected_names.add(index_name)
                index_raw = _read_regular_at(
                    current_fd,
                    index_name,
                    maximum_bytes=MAX_PART_BYTES,
                )
                if (
                    sha256_bytes(index_raw) != part["index_digest"]
                    or len(index_raw) != part["index_bytes"]
                ):
                    raise AutoRuntimeError(
                        "RUN_LOG_INDEX_PHYSICAL_DIGEST_MISMATCH"
                    )
                index_rows = _validate_jsonl(
                    index_raw,
                    contract=self.contract,
                    schema_id=INDEX_ENTRY_SCHEMA,
                    bundle_digest=self.bundle_digest,
                )
                if len(index_rows) != part["index_record_count"]:
                    raise AutoRuntimeError(
                        "RUN_LOG_INDEX_RECORD_COUNT_MISMATCH"
                    )
                if [row["line_number"] for row in index_rows] != list(
                    range(1, len(index_rows) + 1)
                ) or any(
                    row["part_number"] != number for row in index_rows
                ):
                    raise AutoRuntimeError(
                        "RUN_LOG_INDEX_POSITION_CLOSURE_INVALID"
                    )
                ordering = [_event_key(row) for row in index_rows]
                if ordering != sorted(ordering) or (
                    last_key is not None and ordering[0] <= last_key
                ):
                    raise AutoRuntimeError(
                        "RUN_LOG_INDEX_GLOBAL_ORDER_INVALID"
                    )
                for row in index_rows:
                    uid = str(row["event_uid"])
                    digest = str(row["event_digest"])
                    if uid in known:
                        raise AutoRuntimeError(
                            "RUN_LOG_INDEX_EVENT_UID_DUPLICATE"
                        )
                    if row["event_type"] == "BINDING_CORRECTION":
                        if known.get(
                            str(row["supersedes_event_uid"])
                        ) != row["supersedes_event_digest"]:
                            raise AutoRuntimeError(
                                "RUN_LOG_INDEX_CORRECTION_TARGET_NOT_EXACT"
                            )
                    known[uid] = digest
                last_key = ordering[-1]
                all_entries.extend(index_rows)

                if (
                    index_rows[0]["event_uid"]
                    != part["first_event_uid"]
                    or index_rows[0]["event_digest"]
                    != part["first_event_digest"]
                    or index_rows[0]["occurred_at"]
                    != part["first_occurred_at"]
                    or index_rows[-1]["event_uid"]
                    != part["last_event_uid"]
                    or index_rows[-1]["event_digest"]
                    != part["last_event_digest"]
                    or index_rows[-1]["occurred_at"]
                    != part["last_occurred_at"]
                ):
                    raise AutoRuntimeError(
                        "RUN_LOG_INDEX_MANIFEST_RANGE_MISMATCH"
                    )

                if part["state"] == "ACTIVE":
                    expected_names.add(part_name)
                    part_raw = _read_regular_at(
                        current_fd,
                        part_name,
                        maximum_bytes=MAX_PART_BYTES,
                    )
                    if (
                        sha256_bytes(part_raw) != part["shard_digest"]
                        or len(part_raw) != part["shard_bytes"]
                    ):
                        raise AutoRuntimeError(
                            "RUN_LOG_SHARD_PHYSICAL_DIGEST_MISMATCH"
                        )
                    event_rows = _validate_jsonl(
                        part_raw,
                        contract=self.contract,
                        schema_id=PUBLIC_RUN_EVENT_SCHEMA,
                        bundle_digest=self.bundle_digest,
                    )
                    if len(event_rows) != part["record_count"]:
                        raise AutoRuntimeError(
                            "RUN_LOG_SHARD_RECORD_COUNT_MISMATCH"
                        )
                    compared = (
                        "event_uid",
                        "event_digest",
                        "event_type",
                        "occurred_at",
                        "supersedes_event_uid",
                        "supersedes_event_digest",
                    )
                    if any(
                        any(
                            event.get(field) != index.get(field)
                            for field in compared
                        )
                        for event, index in zip(event_rows, index_rows)
                    ):
                        raise AutoRuntimeError(
                            "RUN_LOG_INDEX_EVENT_CLOSURE_MISMATCH"
                        )
                elif part_name in names:
                    raise AutoRuntimeError(
                        "RUN_LOG_PRUNED_SHARD_STILL_PRESENT"
                    )
                if part["state"] == "PRUNED":
                    receipt_path = str(
                        part["retention_receipt_path"]
                    )
                    expected_prefix = prefix + "/"
                    if not receipt_path.startswith(expected_prefix):
                        raise AutoRuntimeError(
                            "RUN_LOG_RETENTION_RECEIPT_PATH_INVALID"
                        )
                    receipt_name = receipt_path[len(expected_prefix) :]
                    if not RETENTION_NAME_RE.fullmatch(receipt_name):
                        raise AutoRuntimeError(
                            "RUN_LOG_RETENTION_RECEIPT_PATH_INVALID"
                        )
                    expected_names.add(receipt_name)
                    receipt = receipts.get(receipt_name)
                    if receipt is None:
                        receipt_raw = _read_regular_at(
                            current_fd,
                            receipt_name,
                            maximum_bytes=1024 * 1024,
                        )
                        try:
                            parsed_receipt = parse_json_bytes(
                                receipt_raw
                            )
                        except Exception as exc:
                            raise AutoRuntimeError(
                                "RUN_LOG_RETENTION_RECEIPT_JSON_INVALID"
                            ) from exc
                        if (
                            not isinstance(parsed_receipt, dict)
                            or canonicalize_object(parsed_receipt)
                            != receipt_raw
                        ):
                            raise AutoRuntimeError(
                                "RUN_LOG_RETENTION_RECEIPT_NOT_EXACT_JCS"
                            )
                        validate_public_serialization(
                            receipt_raw,
                            self.contract,
                            RETENTION_RECEIPT_SCHEMA,
                            self.bundle_digest,
                        )
                        receipt = MappingProxyType(parsed_receipt)
                        receipts[receipt_name] = receipt
                    if (
                        receipt["receipt_uid"]
                        != part["retention_receipt_uid"]
                        or receipt["receipt_digest"]
                        != part["retention_receipt_digest"]
                        or receipt["executed_at"] != part["pruned_at"]
                    ):
                        raise AutoRuntimeError(
                            "RUN_LOG_RETENTION_RECEIPT_IDENTITY_MISMATCH"
                        )
                    affected = [
                        item
                        for item in receipt[
                            "affected_public_artifacts"
                        ]
                        if item["artifact_repo_path"]
                        == f"{prefix}/{part_name}"
                    ]
                    prior_digest = prune_prior_digests.get(number)
                    if (
                        len(affected) != 1
                        or prior_digest is None
                    ):
                        raise AutoRuntimeError(
                            "RUN_LOG_RETENTION_RECEIPT_PART_NOT_EXACT"
                        )
                    item = affected[0]
                    expected = {
                        "prior_artifact_digest": part[
                            "shard_digest"
                        ],
                        "prior_artifact_bytes": part["shard_bytes"],
                        "prior_record_count": part["record_count"],
                        "first_published_at": part[
                            "first_published_at"
                        ],
                        "retention_not_before": part[
                            "retention_not_before"
                        ],
                        "retained_index_path": (
                            f"{prefix}/{index_name}"
                        ),
                        "retained_index_digest": part[
                            "index_digest"
                        ],
                        "prior_daily_manifest_digest": prior_digest,
                    }
                    if any(
                        item.get(field) != value
                        for field, value in expected.items()
                    ):
                        raise AutoRuntimeError(
                            "RUN_LOG_RETENTION_RECEIPT_PART_MISMATCH"
                        )
                if (
                    f"{prefix}/{index_name}".rsplit("/", 1)[0]
                    != f"{prefix}/{part_name}".rsplit("/", 1)[0]
                ):
                    raise AutoRuntimeError(
                        "RUN_LOG_PART_INDEX_DATE_MISMATCH"
                    )

            if set(names) != expected_names:
                raise AutoRuntimeError(
                    "RUN_LOG_TREE_PHYSICAL_SET_MISMATCH"
                )
            assert last_key is not None
            return ExistingDailyTree(
                local_date,
                f"{prefix}/{latest_name}",
                latest_raw,
                MappingProxyType(latest),
                tuple(all_entries),
                MappingProxyType(known),
                last_key,
            )
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)


class DailyRunShardWriter:
    """Build exact append-only daily artifacts without performing I/O."""

    def __init__(
        self,
        contract: AutoContract,
        bundle_digest: str,
        *,
        partition_byte_limit: int = MAX_PART_BYTES,
    ) -> None:
        if (
            partition_byte_limit < 1
            or partition_byte_limit > MAX_PART_BYTES
        ):
            raise AutoRuntimeError("RUN_LOG_PARTITION_LIMIT_INVALID")
        self.contract = contract
        self.bundle_digest = bundle_digest
        self.partition_byte_limit = partition_byte_limit

    def _validate_event(
        self,
        event: Mapping[str, Any],
    ) -> Tuple[Mapping[str, Any], bytes]:
        raw = canonicalize_object(event)
        parsed = validate_public_serialization(
            raw,
            self.contract,
            PUBLIC_RUN_EVENT_SCHEMA,
            self.bundle_digest,
        )
        return MappingProxyType(dict(parsed)), raw + b"\n"

    def _index_entry(
        self,
        event: Mapping[str, Any],
        *,
        part_number: int,
        line_number: int,
        first_published_at: str,
    ) -> Tuple[Mapping[str, Any], bytes]:
        value: Dict[str, Any] = {
            "schema_version": INDEX_ENTRY_SCHEMA,
            "protocol_revision": PROTOCOL,
            "bundle_digest": self.bundle_digest,
            "event_uid": event["event_uid"],
            "event_digest": event["event_digest"],
            "event_type": event["event_type"],
            "occurred_at": event["occurred_at"],
            "part_number": part_number,
            "line_number": line_number,
            "first_published_at": first_published_at,
            "index_entry_digest": "0" * 64,
        }
        if event["event_type"] == "BINDING_CORRECTION":
            value["supersedes_event_uid"] = event[
                "supersedes_event_uid"
            ]
            value["supersedes_event_digest"] = event[
                "supersedes_event_digest"
            ]
        value = canonical_with_digest(value, "index_entry_digest")
        raw = canonicalize_object(value)
        validate_public_serialization(
            raw,
            self.contract,
            INDEX_ENTRY_SCHEMA,
            self.bundle_digest,
        )
        return MappingProxyType(value), raw + b"\n"

    def plan(
        self,
        events: Sequence[Mapping[str, Any]],
        *,
        manifest_uid: str,
        auto_transaction_uid: str,
        publication_transaction_at: dt.datetime,
        previous: Optional[ExistingDailyTree] = None,
    ) -> RunLogWritePlan:
        published_at = format_utc(publication_transaction_at)
        if previous is not None:
            validate_public_serialization(
                previous.manifest_raw,
                self.contract,
                DAILY_MANIFEST_SCHEMA,
                self.bundle_digest,
            )
            if (
                canonicalize_object(dict(previous.manifest))
                != previous.manifest_raw
                or publication_transaction_at
                <= parse_utc(
                    str(
                        previous.manifest[
                            "publication_transaction_at"
                        ]
                    )
                )
            ):
                raise AutoRuntimeError(
                    "RUN_LOG_MANIFEST_APPEND_TRANSACTION_INVALID"
                )
        validated = [self._validate_event(event) for event in events]
        validated.sort(key=lambda pair: _event_key(pair[0]))
        known = dict(previous.event_digests) if previous else {}
        accepted = []
        deduplicated = 0
        observed_input: Dict[str, str] = {}
        local_date: Optional[str] = (
            previous.local_date if previous is not None else None
        )
        for event, raw in validated:
            event_date = _sydney_date(str(event["occurred_at"]))
            if local_date is None:
                local_date = event_date
            elif event_date != local_date:
                raise AutoRuntimeError(
                    "RUN_LOG_PLAN_MULTIPLE_LOCAL_DATES"
                )
            uid = str(event["event_uid"])
            digest = str(event["event_digest"])
            input_digest = observed_input.get(uid)
            if input_digest is not None:
                if input_digest != digest:
                    raise AutoRuntimeError(
                        "RUN_LOG_INPUT_EVENT_UID_DIGEST_CONFLICT"
                    )
                deduplicated += 1
                continue
            observed_input[uid] = digest
            existing = known.get(uid)
            if existing is not None:
                if existing != digest:
                    raise AutoRuntimeError(
                        "RUN_LOG_EXISTING_EVENT_UID_DIGEST_CONFLICT"
                    )
                deduplicated += 1
                continue
            if event["event_type"] == "BINDING_CORRECTION":
                if known.get(
                    str(event["supersedes_event_uid"])
                ) != event["supersedes_event_digest"]:
                    raise AutoRuntimeError(
                        "RUN_LOG_CORRECTION_TARGET_NOT_EXACT"
                    )
            if parse_utc(str(event["occurred_at"])) > (
                publication_transaction_at
            ):
                raise AutoRuntimeError(
                    "RUN_LOG_EVENT_AFTER_PUBLICATION_TRANSACTION"
                )
            known[uid] = digest
            accepted.append((event, raw))
        if not accepted:
            raise AutoRuntimeError("RUN_LOG_NO_NEW_EVENTS")
        assert local_date is not None
        _canonical_date(local_date)
        if previous is not None and (
            _event_key(accepted[0][0]) <= previous.last_event_key
        ):
            raise AutoRuntimeError("RUN_LOG_APPEND_ORDER_VIOLATION")

        prior_parts = (
            copy.deepcopy(list(previous.manifest["parts"]))
            if previous is not None
            else []
        )
        first_part_number = len(prior_parts) + 1
        if first_part_number > MAX_SEQUENCE:
            raise AutoRuntimeError("RUN_LOG_PART_SEQUENCE_EXHAUSTED")

        chunks = []
        current = []
        current_shard_bytes = 0
        current_index_bytes = 0
        part_number = first_part_number
        for event, event_raw in accepted:
            line_number = len(current) + 1
            index, index_raw = self._index_entry(
                event,
                part_number=part_number,
                line_number=line_number,
                first_published_at=published_at,
            )
            if current and (
                current_shard_bytes + len(event_raw)
                > self.partition_byte_limit
                or current_index_bytes + len(index_raw)
                > self.partition_byte_limit
            ):
                chunks.append(current)
                part_number += 1
                if part_number > MAX_SEQUENCE:
                    raise AutoRuntimeError(
                        "RUN_LOG_PART_SEQUENCE_EXHAUSTED"
                    )
                current = []
                current_shard_bytes = 0
                current_index_bytes = 0
                index, index_raw = self._index_entry(
                    event,
                    part_number=part_number,
                    line_number=1,
                    first_published_at=published_at,
                )
            if (
                len(event_raw) > self.partition_byte_limit
                or len(index_raw) > self.partition_byte_limit
            ):
                raise AutoRuntimeError(
                    "RUN_LOG_SINGLE_RECORD_EXCEEDS_PART_LIMIT"
                )
            current.append((event, event_raw, index, index_raw))
            current_shard_bytes += len(event_raw)
            current_index_bytes += len(index_raw)
        chunks.append(current)

        date = _canonical_date(local_date)
        prefix = (
            f"{RUN_LOG_ROOT}/{date.year:04d}/"
            f"{date.month:02d}/{date.day:02d}"
        )
        artifacts = []
        new_parts = []
        for offset, chunk in enumerate(chunks):
            number = first_part_number + offset
            shard_name = f"part-{number:04d}.jsonl"
            index_name = f"index-{number:04d}.jsonl"
            shard_raw = b"".join(item[1] for item in chunk)
            index_raw = b"".join(item[3] for item in chunk)
            event_rows = [item[0] for item in chunk]
            index_rows = [item[2] for item in chunk]
            if (
                len(shard_raw) > MAX_PART_BYTES
                or len(index_raw) > MAX_PART_BYTES
            ):
                raise AutoRuntimeError("RUN_LOG_PART_SIZE_EXCEEDED")
            _validate_jsonl(
                shard_raw,
                contract=self.contract,
                schema_id=PUBLIC_RUN_EVENT_SCHEMA,
                bundle_digest=self.bundle_digest,
            )
            _validate_jsonl(
                index_raw,
                contract=self.contract,
                schema_id=INDEX_ENTRY_SCHEMA,
                bundle_digest=self.bundle_digest,
            )
            first = event_rows[0]
            last = event_rows[-1]
            new_parts.append(
                {
                    "part_number": number,
                    "shard_name": shard_name,
                    "state": "ACTIVE",
                    "shard_digest": sha256_bytes(shard_raw),
                    "shard_bytes": len(shard_raw),
                    "record_count": len(event_rows),
                    "index_name": index_name,
                    "index_digest": sha256_bytes(index_raw),
                    "index_bytes": len(index_raw),
                    "index_record_count": len(index_rows),
                    "first_event_uid": first["event_uid"],
                    "first_event_digest": first["event_digest"],
                    "first_occurred_at": first["occurred_at"],
                    "last_event_uid": last["event_uid"],
                    "last_event_digest": last["event_digest"],
                    "last_occurred_at": last["occurred_at"],
                    "first_published_at": published_at,
                    "retention_not_before": format_utc(
                        publication_transaction_at + RETENTION_AGE
                    ),
                }
            )
            artifacts.extend(
                (
                    RunLogArtifact(
                        f"{prefix}/{shard_name}",
                        PUBLIC_RUN_EVENT_SCHEMA,
                        JSONL_SERIALIZATION,
                        shard_raw,
                        len(event_rows),
                    ),
                    RunLogArtifact(
                        f"{prefix}/{index_name}",
                        INDEX_ENTRY_SCHEMA,
                        JSONL_SERIALIZATION,
                        index_raw,
                        len(index_rows),
                    ),
                )
            )

        parts = prior_parts + new_parts
        active = [part for part in parts if part["state"] == "ACTIVE"]
        pruned = [part for part in parts if part["state"] == "PRUNED"]
        revision = (
            int(previous.manifest["manifest_revision"]) + 1
            if previous is not None
            else 1
        )
        if revision > MAX_SEQUENCE:
            raise AutoRuntimeError("RUN_LOG_MANIFEST_SEQUENCE_EXHAUSTED")
        previous_digest = (
            str(previous.manifest["manifest_digest"])
            if previous is not None
            else None
        )
        manifest = canonical_with_digest(
            {
                "schema_version": DAILY_MANIFEST_SCHEMA,
                "protocol_revision": PROTOCOL,
                "bundle_digest": self.bundle_digest,
                "manifest_uid": manifest_uid,
                "local_date": local_date,
                "timezone": "Australia/Sydney",
                "record_schema_id": PUBLIC_RUN_EVENT_SCHEMA,
                "artifact_serialization": JSONL_SERIALIZATION,
                "max_part_bytes": MAX_PART_BYTES,
                "manifest_revision": revision,
                "previous_manifest_digest": previous_digest,
                "auto_transaction_uid": auto_transaction_uid,
                "publication_transaction_at": published_at,
                "max_part_number": len(parts),
                "total_part_count": len(parts),
                "active_part_count": len(active),
                "pruned_part_count": len(pruned),
                "active_shard_bytes": sum(
                    part["shard_bytes"] for part in active
                ),
                "active_record_count": sum(
                    part["record_count"] for part in active
                ),
                "retained_index_bytes": sum(
                    part["index_bytes"] for part in parts
                ),
                "retained_index_record_count": sum(
                    part["index_record_count"] for part in parts
                ),
                "parts": parts,
                "manifest_digest": "0" * 64,
            },
            "manifest_digest",
        )
        manifest_raw = canonicalize_object(manifest)
        validate_public_serialization(
            manifest_raw,
            self.contract,
            DAILY_MANIFEST_SCHEMA,
            self.bundle_digest,
        )
        artifacts.append(
            RunLogArtifact(
                f"{prefix}/manifest-{revision:04d}.json",
                DAILY_MANIFEST_SCHEMA,
                OBJECT_SERIALIZATION,
                manifest_raw,
                1,
            )
        )
        artifacts.sort(key=lambda artifact: artifact.relative_path)
        return RunLogWritePlan(
            local_date,
            revision,
            previous_digest,
            MappingProxyType(manifest),
            tuple(artifacts),
            len(events),
            deduplicated,
            len(accepted),
        )
