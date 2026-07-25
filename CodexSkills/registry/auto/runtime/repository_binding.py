"""Fail-closed repository binding for the canonical AU-040 run-log lane.

The module does not resolve Skill identities.  That resolver remains owned by
Mechanism.  It only consumes an externally pinned control decision, proves the
local reference repository without network access, and issues an in-process
permit that cannot be replaced by caller booleans or digest maps.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

from CodexSkills.governance.tools.canonical_json import (
    canonicalize_object,
    parse_json_bytes,
)

from .bootstrap import (
    BootstrapContext,
    require_repository_binding_authority,
)
from .core import AutoRuntimeError
from .privacy import (
    validate_public_jsonl_serialization,
    validate_public_serialization,
)


REPOSITORY_ID = "github.com/LinzeColin/AgentDatabase"
REMOTE_NAME = "origin"
REMOTE_URL = "git@github.com:LinzeColin/AgentDatabase.git"
REFERENCE_BRANCH = "main"
REMOTE_REF = "refs/heads/main"
PUSH_REFSPEC = "HEAD:main"
OBJECT_FORMAT = "sha1"
RUN_LOG_ROOT = "OpenAIDatabase/data/run_logs/skills_runs"
SYDNEY = ZoneInfo("Australia/Sydney")
MAX_JSONL_BYTES = 20 * 1024 * 1024
MAX_OBJECT_BYTES = 1024 * 1024
MAX_SEQUENCE = 9999
OBJECT_SERIALIZATION = "RFC8785_JCS_OBJECT"
JSONL_SERIALIZATION = "RFC8785_JCS_PER_LINE_LF"
PUBLIC_RUN_EVENT_SCHEMA = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:public-run-event:v2"
)
INDEX_ENTRY_SCHEMA = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:run-event-index-entry:v1"
)
DAILY_MANIFEST_SCHEMA = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:daily-run-shard-manifest:v1"
)
RETENTION_RECEIPT_SCHEMA = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:retention-receipt:v3"
)
TAGGED_HEAD_RE = re.compile(r"^sha1:([0-9a-f]{40})$")
RUN_LOG_PATH_RE = re.compile(
    r"^"
    + re.escape(RUN_LOG_ROOT)
    + r"/([0-9]{4})/([0-9]{2})/([0-9]{2})/"
    r"(part|index|manifest|retention-receipt)-([0-9]{4})"
    r"(\.jsonl|\.json)$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PERMIT_SEAL = object()


@dataclass(frozen=True)
class RepositoryBindingInputs:
    """Repo-external, per-transaction binding inputs."""

    repo_root: Path
    scratch_root: Path
    state_root: Path
    expected_remote_head: str


@dataclass(frozen=True)
class RepositoryBindingObservation:
    repository_id: str
    repo_root: Path
    scratch_root: Path
    state_root: Path
    expected_remote_head: str
    object_format: str
    remote_name: str
    fetch_url: str
    push_url: str
    branch: str
    remote_ref: str
    push_refspec: str
    reference_tree_clean: bool
    network_accessed: bool


class RepositoryBindingPermit:
    """Opaque proof issued only after control authority and local probe pass."""

    __slots__ = ("_seal", "context", "observation")

    def __init__(
        self,
        seal: object,
        context: BootstrapContext,
        observation: RepositoryBindingObservation,
    ) -> None:
        if seal is not _PERMIT_SEAL:
            raise AutoRuntimeError(
                "REPOSITORY_BINDING_PERMIT_CONSTRUCTION_FORBIDDEN"
            )
        self._seal = seal
        self.context = context
        self.observation = observation


def _run_git_readonly(
    repo_root: Path,
    *args: str,
) -> bytes:
    allowed = {
        ("rev-parse", "--show-toplevel"),
        ("rev-parse", "--show-object-format"),
        ("symbolic-ref", "--quiet", "--short", "HEAD"),
        (
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ),
        ("remote", "get-url", REMOTE_NAME),
        ("remote", "get-url", "--push", REMOTE_NAME),
        ("show-ref", "--verify", "--hash", REMOTE_REF),
    }
    if tuple(args) not in allowed:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_GIT_COMMAND_NOT_READONLY"
        )
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
            env={
                **os.environ,
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_OPTIONAL_LOCKS": "0",
            },
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_GIT_READ_UNAVAILABLE"
        ) from exc
    if (
        completed.returncode != 0
        or len(completed.stdout) > 1024 * 1024
        or len(completed.stderr) > 64 * 1024
    ):
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_GIT_READ_FAILED"
        )
    return completed.stdout


def _one_line(raw: bytes, code: str) -> str:
    try:
        value = raw.decode("utf-8", errors="strict").rstrip("\n")
    except UnicodeDecodeError as exc:
        raise AutoRuntimeError(code) from exc
    if not value or "\n" in value or "\r" in value:
        raise AutoRuntimeError(code)
    return value


def _contains(root: Path, candidate: Path) -> bool:
    try:
        return (
            os.path.commonpath((str(root), str(candidate)))
            == str(root)
        )
    except ValueError:
        return False


def _real_directory(path: Path, code: str) -> Path:
    if not path.is_absolute():
        raise AutoRuntimeError(code + "_NOT_ABSOLUTE")
    try:
        before = os.lstat(str(path))
    except OSError as exc:
        raise AutoRuntimeError(code + "_LSTAT_FAILED") from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
        raise AutoRuntimeError(code + "_NOT_REAL_DIRECTORY")
    try:
        resolved = path.resolve(strict=True)
        after = os.lstat(str(resolved))
    except OSError as exc:
        raise AutoRuntimeError(code + "_REALPATH_FAILED") from exc
    if (
        stat.S_ISLNK(after.st_mode)
        or not stat.S_ISDIR(after.st_mode)
        or (before.st_dev, before.st_ino)
        != (after.st_dev, after.st_ino)
    ):
        raise AutoRuntimeError(code + "_REBOUND")
    return resolved


def _external_candidate(
    path: Path,
    code: str,
    *,
    must_exist: bool,
) -> Path:
    if not path.is_absolute() or path.name in {"", ".", ".."}:
        raise AutoRuntimeError(code + "_INVALID")
    try:
        info = os.lstat(str(path))
    except FileNotFoundError:
        if must_exist:
            raise AutoRuntimeError(code + "_MISSING")
        parent = _real_directory(path.parent, code + "_PARENT")
        return parent / path.name
    except OSError as exc:
        raise AutoRuntimeError(code + "_LSTAT_FAILED") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise AutoRuntimeError(code + "_NOT_REAL_DIRECTORY")
    return _real_directory(path, code)


def probe_repository_binding(
    inputs: RepositoryBindingInputs,
) -> RepositoryBindingObservation:
    """Prove the local reference repo without a network or mutable Git call."""

    match = TAGGED_HEAD_RE.fullmatch(inputs.expected_remote_head)
    if not match:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_EXPECTED_HEAD_INVALID"
        )
    repo = _real_directory(
        inputs.repo_root,
        "REPOSITORY_BINDING_REPO_ROOT",
    )
    observed_top = _one_line(
        _run_git_readonly(repo, "rev-parse", "--show-toplevel"),
        "REPOSITORY_BINDING_TOPLEVEL_INVALID",
    )
    try:
        observed_top_path = Path(observed_top).resolve(strict=True)
    except OSError as exc:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_TOPLEVEL_INVALID"
        ) from exc
    if observed_top_path != repo:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_TOPLEVEL_MISMATCH"
        )
    object_format = _one_line(
        _run_git_readonly(
            repo,
            "rev-parse",
            "--show-object-format",
        ),
        "REPOSITORY_BINDING_OBJECT_FORMAT_INVALID",
    )
    if object_format != OBJECT_FORMAT:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_OBJECT_FORMAT_MISMATCH"
        )
    branch = _one_line(
        _run_git_readonly(
            repo,
            "symbolic-ref",
            "--quiet",
            "--short",
            "HEAD",
        ),
        "REPOSITORY_BINDING_BRANCH_INVALID",
    )
    if branch != REFERENCE_BRANCH:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_BRANCH_MISMATCH"
        )
    fetch_url = _one_line(
        _run_git_readonly(
            repo,
            "remote",
            "get-url",
            REMOTE_NAME,
        ),
        "REPOSITORY_BINDING_FETCH_URL_INVALID",
    )
    push_url = _one_line(
        _run_git_readonly(
            repo,
            "remote",
            "get-url",
            "--push",
            REMOTE_NAME,
        ),
        "REPOSITORY_BINDING_PUSH_URL_INVALID",
    )
    if fetch_url != REMOTE_URL or push_url != REMOTE_URL:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_REMOTE_URL_MISMATCH"
        )
    local_main = _one_line(
        _run_git_readonly(
            repo,
            "show-ref",
            "--verify",
            "--hash",
            REMOTE_REF,
        ),
        "REPOSITORY_BINDING_MAIN_REF_INVALID",
    )
    if local_main != match.group(1):
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_EXPECTED_HEAD_MISMATCH"
        )
    if _run_git_readonly(
        repo,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    ):
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_REFERENCE_TREE_DIRTY"
        )

    scratch = _external_candidate(
        inputs.scratch_root,
        "REPOSITORY_BINDING_SCRATCH_ROOT",
        must_exist=True,
    )
    state = _external_candidate(
        inputs.state_root,
        "REPOSITORY_BINDING_STATE_ROOT",
        must_exist=False,
    )
    if (
        _contains(repo, scratch)
        or _contains(scratch, repo)
        or _contains(repo, state)
        or _contains(state, repo)
        or _contains(scratch, state)
        or _contains(state, scratch)
    ):
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_ROOT_CONTAINMENT_INVALID"
        )
    return RepositoryBindingObservation(
        REPOSITORY_ID,
        repo,
        scratch,
        state,
        inputs.expected_remote_head,
        object_format,
        REMOTE_NAME,
        fetch_url,
        push_url,
        branch,
        REMOTE_REF,
        PUSH_REFSPEC,
        True,
        False,
    )


def authorize_repository_binding(
    context: BootstrapContext,
    inputs: RepositoryBindingInputs,
) -> RepositoryBindingPermit:
    """Consume the externally pinned Mechanism gate, then probe locally."""

    require_repository_binding_authority(context)
    observation = probe_repository_binding(inputs)
    return RepositoryBindingPermit(_PERMIT_SEAL, context, observation)


def assert_repository_binding_permit(
    permit: Optional[RepositoryBindingPermit],
    context: BootstrapContext,
    expected_remote_head: str,
) -> RepositoryBindingObservation:
    if (
        not isinstance(permit, RepositoryBindingPermit)
        or permit._seal is not _PERMIT_SEAL
        or permit.context is not context
        or permit.observation.expected_remote_head
        != expected_remote_head
        or permit.observation.network_accessed
    ):
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_PERMIT_REQUIRED"
        )
    return permit.observation


def _artifact_kind(
    path: str,
) -> Tuple[str, str, int]:
    match = RUN_LOG_PATH_RE.fullmatch(path)
    if not match:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_RUN_LOG_PATH_INVALID"
        )
    year, month, day, kind, sequence_raw, extension = match.groups()
    try:
        local_date = dt.date(int(year), int(month), int(day))
    except ValueError as exc:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_RUN_LOG_DATE_INVALID"
        ) from exc
    sequence = int(sequence_raw)
    if sequence < 1 or sequence > MAX_SEQUENCE:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_RUN_LOG_SEQUENCE_INVALID"
        )
    expected_extension = (
        ".jsonl" if kind in {"part", "index"} else ".json"
    )
    if extension != expected_extension:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_RUN_LOG_EXTENSION_INVALID"
        )
    return local_date.isoformat(), kind, sequence


def _artifact_contract(kind: str) -> Tuple[str, str, int]:
    return {
        "part": (
            PUBLIC_RUN_EVENT_SCHEMA,
            JSONL_SERIALIZATION,
            MAX_JSONL_BYTES,
        ),
        "index": (
            INDEX_ENTRY_SCHEMA,
            JSONL_SERIALIZATION,
            MAX_JSONL_BYTES,
        ),
        "manifest": (
            DAILY_MANIFEST_SCHEMA,
            OBJECT_SERIALIZATION,
            MAX_OBJECT_BYTES,
        ),
        "retention-receipt": (
            RETENTION_RECEIPT_SCHEMA,
            OBJECT_SERIALIZATION,
            MAX_OBJECT_BYTES,
        ),
    }[kind]


def _parse_jsonl(raw: bytes) -> Tuple[Mapping[str, Any], ...]:
    if not raw or not raw.endswith(b"\n"):
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_JSONL_FRAMING_INVALID"
        )
    rows = []
    for line in raw[:-1].split(b"\n"):
        if not line:
            raise AutoRuntimeError(
                "REPOSITORY_BINDING_JSONL_FRAMING_INVALID"
            )
        try:
            parsed = parse_json_bytes(line)
        except Exception as exc:
            raise AutoRuntimeError(
                "REPOSITORY_BINDING_JSONL_INVALID"
            ) from exc
        if (
            not isinstance(parsed, dict)
            or canonicalize_object(parsed) != line
        ):
            raise AutoRuntimeError(
                "REPOSITORY_BINDING_JSONL_NOT_EXACT_JCS"
            )
        rows.append(MappingProxyType(parsed))
    return tuple(rows)


def _sydney_date(value: str) -> str:
    try:
        observed = dt.datetime.strptime(
            value,
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ).replace(tzinfo=dt.timezone.utc)
    except (TypeError, ValueError) as exc:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_EVENT_TIME_INVALID"
        ) from exc
    return observed.astimezone(SYDNEY).date().isoformat()


def validate_run_log_transaction(
    permit: RepositoryBindingPermit,
    context: BootstrapContext,
    expected_remote_head: str,
    artifacts: Sequence[Any],
) -> Mapping[str, Any]:
    """Validate the exact AU-040 changed-artifact closure before locking."""

    assert_repository_binding_permit(
        permit,
        context,
        expected_remote_head,
    )
    if not artifacts:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_RUN_LOG_TRANSACTION_EMPTY"
        )
    rows = []
    dates = set()
    manifests = []
    receipts = {}
    parts = {}
    indexes = {}
    deletes = {}
    seen_paths = set()
    for artifact in artifacts:
        path = getattr(artifact, "relative_path", None)
        if not isinstance(path, str) or path in seen_paths:
            raise AutoRuntimeError(
                "REPOSITORY_BINDING_ARTIFACT_PATH_INVALID"
            )
        seen_paths.add(path)
        local_date, kind, sequence = _artifact_kind(path)
        dates.add(local_date)
        expected_schema, expected_serialization, maximum = (
            _artifact_contract(kind)
        )
        operation = getattr(artifact, "operation", None)
        payload = getattr(artifact, "payload", None)
        if (
            getattr(artifact, "lane", None) != "RUN_LOG"
            or getattr(artifact, "schema_id", None)
            != expected_schema
            or operation not in {"PUT", "DELETE"}
        ):
            raise AutoRuntimeError(
                "REPOSITORY_BINDING_ARTIFACT_CONTRACT_MISMATCH"
            )
        if operation == "DELETE":
            if (
                kind != "part"
                or payload is not None
                or getattr(artifact, "prior_serialization", None)
                != expected_serialization
                or not SHA256_RE.fullmatch(
                    str(getattr(artifact, "prior_digest", ""))
                )
                or not isinstance(
                    getattr(artifact, "prior_bytes", None),
                    int,
                )
                or not isinstance(
                    getattr(artifact, "prior_record_count", None),
                    int,
                )
            ):
                raise AutoRuntimeError(
                    "REPOSITORY_BINDING_DELETE_CONTRACT_INVALID"
                )
            deletes[sequence] = artifact
        else:
            if (
                not isinstance(payload, bytes)
                or not payload
                or len(payload) > maximum
                or getattr(artifact, "serialization", None)
                != expected_serialization
            ):
                raise AutoRuntimeError(
                    "REPOSITORY_BINDING_PUT_CONTRACT_INVALID"
                )
            if expected_serialization == OBJECT_SERIALIZATION:
                if payload.endswith(b"\n"):
                    raise AutoRuntimeError(
                        "REPOSITORY_BINDING_OBJECT_TRAILING_LF"
                    )
                try:
                    parsed = parse_json_bytes(payload)
                except Exception as exc:
                    raise AutoRuntimeError(
                        "REPOSITORY_BINDING_OBJECT_INVALID"
                    ) from exc
                if (
                    not isinstance(parsed, dict)
                    or canonicalize_object(parsed) != payload
                ):
                    raise AutoRuntimeError(
                        "REPOSITORY_BINDING_OBJECT_NOT_EXACT_JCS"
                    )
                parsed_value: Any = MappingProxyType(
                    validate_public_serialization(
                        payload,
                        context.contract,
                        expected_schema,
                        context.trust.expected_bundle_digest,
                    )
                )
            else:
                parsed_value = (
                    validate_public_jsonl_serialization(
                        payload,
                        context.contract,
                        expected_schema,
                        context.trust.expected_bundle_digest,
                        maximum_bytes=maximum,
                    )
                )
            if kind == "manifest":
                manifests.append((sequence, artifact, parsed_value))
            elif kind == "retention-receipt":
                receipts[path] = (sequence, artifact, parsed_value)
            elif kind == "part":
                parts[sequence] = (artifact, parsed_value)
            else:
                indexes[sequence] = (artifact, parsed_value)
        rows.append((path, local_date, kind, sequence, operation))

    if len(dates) != 1 or len(manifests) != 1:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_DAILY_TRANSACTION_CLOSURE_INVALID"
        )
    local_date = next(iter(dates))
    manifest_sequence, manifest_artifact, manifest = manifests[0]
    if (
        manifest.get("local_date") != local_date
        or manifest.get("manifest_revision") != manifest_sequence
    ):
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_MANIFEST_IDENTITY_MISMATCH"
        )
    manifest_parts = manifest.get("parts")
    if not isinstance(manifest_parts, list) or not manifest_parts:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_MANIFEST_PARTS_INVALID"
        )
    numbers = [item.get("part_number") for item in manifest_parts]
    if numbers != list(range(1, len(numbers) + 1)):
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_MANIFEST_NUMBERING_INVALID"
        )
    part_entries = {
        int(item["part_number"]): item for item in manifest_parts
    }
    if set(parts) != set(indexes):
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_PART_INDEX_PUT_SET_MISMATCH"
        )
    for number, (part_artifact, part_rows) in parts.items():
        entry = part_entries.get(number)
        index_artifact, index_rows = indexes[number]
        if (
            entry is None
            or entry.get("state") != "ACTIVE"
            or entry.get("shard_name")
            != f"part-{number:04d}.jsonl"
            or entry.get("index_name")
            != f"index-{number:04d}.jsonl"
            or entry.get("shard_digest")
            != hashlib.sha256(part_artifact.payload).hexdigest()
            or entry.get("shard_bytes")
            != len(part_artifact.payload)
            or entry.get("record_count") != len(part_rows)
            or entry.get("index_digest")
            != hashlib.sha256(index_artifact.payload).hexdigest()
            or entry.get("index_bytes")
            != len(index_artifact.payload)
            or entry.get("index_record_count") != len(index_rows)
            or len(part_rows) != len(index_rows)
        ):
            raise AutoRuntimeError(
                "REPOSITORY_BINDING_PART_INDEX_MANIFEST_MISMATCH"
            )
        for line_number, (event, index) in enumerate(
            zip(part_rows, index_rows),
            1,
        ):
            if (
                _sydney_date(str(event.get("occurred_at")))
                != local_date
                or _sydney_date(str(index.get("occurred_at")))
                != local_date
                or index.get("part_number") != number
                or index.get("line_number") != line_number
                or index.get("event_uid") != event.get("event_uid")
                or index.get("event_digest")
                != event.get("event_digest")
            ):
                raise AutoRuntimeError(
                    "REPOSITORY_BINDING_EVENT_INDEX_CLOSURE_INVALID"
                )
    referenced_receipts = set()
    for number, deleted in deletes.items():
        entry = part_entries.get(number)
        if (
            entry is None
            or entry.get("state") != "PRUNED"
            or entry.get("shard_name")
            != f"part-{number:04d}.jsonl"
            or entry.get("shard_digest")
            != deleted.prior_digest
            or entry.get("shard_bytes") != deleted.prior_bytes
            or entry.get("record_count")
            != deleted.prior_record_count
        ):
            raise AutoRuntimeError(
                "REPOSITORY_BINDING_DELETE_MANIFEST_MISMATCH"
            )
        receipt_path = entry.get("retention_receipt_path")
        receipt_row = receipts.get(receipt_path)
        if receipt_row is None:
            raise AutoRuntimeError(
                "REPOSITORY_BINDING_DELETE_RECEIPT_REQUIRED"
            )
        _, receipt_artifact, receipt = receipt_row
        if (
            entry.get("retention_receipt_digest")
            != receipt.get("receipt_digest")
            or entry.get("retention_receipt_uid")
            != receipt.get("receipt_uid")
            or entry.get("pruned_at") != receipt.get("executed_at")
        ):
            raise AutoRuntimeError(
                "REPOSITORY_BINDING_DELETE_RECEIPT_MISMATCH"
            )
        affected = [
            item
            for item in receipt.get(
                "affected_public_artifacts",
                [],
            )
            if item.get("artifact_repo_path")
            == deleted.relative_path
        ]
        if (
            len(affected) != 1
            or affected[0].get("prior_artifact_digest")
            != deleted.prior_digest
            or affected[0].get("prior_artifact_bytes")
            != deleted.prior_bytes
            or affected[0].get("prior_record_count")
            != deleted.prior_record_count
            or affected[0].get("retained_index_path")
            != (
                f"{RUN_LOG_ROOT}/{local_date.replace('-', '/')}/"
                f"index-{number:04d}.jsonl"
            )
            or affected[0].get("retained_index_digest")
            != entry.get("index_digest")
            or affected[0].get("prior_daily_manifest_digest")
            != manifest.get("previous_manifest_digest")
        ):
            raise AutoRuntimeError(
                "REPOSITORY_BINDING_DELETE_RECEIPT_CLOSURE_INVALID"
            )
        referenced_receipts.add(receipt_path)
    if set(receipts) != referenced_receipts:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_RETENTION_RECEIPT_UNLISTED"
        )
    if deletes and manifest_sequence <= 1:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_DELETE_PREDECESSOR_REQUIRED"
        )
    return MappingProxyType(
        {
            "artifact_paths": tuple(sorted(seen_paths)),
            "delete_part_numbers": tuple(sorted(deletes)),
            "local_date": local_date,
            "manifest_path": manifest_artifact.relative_path,
            "manifest_revision": manifest_sequence,
            "put_part_numbers": tuple(sorted(parts)),
            "retention_receipt_paths": tuple(sorted(receipts)),
        }
    )


def validate_delete_prerequisites(
    permit: RepositoryBindingPermit,
    context: BootstrapContext,
    expected_remote_head: str,
    closure: Mapping[str, Any],
    artifacts: Sequence[Any],
    read_artifact,
    worktree: Path,
) -> None:
    """Revalidate retained index and prior manifest before any DELETE."""

    assert_repository_binding_permit(
        permit,
        context,
        expected_remote_head,
    )
    deleted = {
        int(_artifact_kind(item.relative_path)[2]): item
        for item in artifacts
        if getattr(item, "operation", None) == "DELETE"
    }
    if not deleted:
        return
    local_prefix = (
        f"{RUN_LOG_ROOT}/"
        f"{str(closure['local_date']).replace('-', '/')}"
    )
    manifest_revision = int(closure["manifest_revision"])
    previous_path = (
        f"{local_prefix}/manifest-{manifest_revision - 1:04d}.json"
    )
    previous_raw = read_artifact(worktree, previous_path)
    try:
        previous = parse_json_bytes(previous_raw)
    except Exception as exc:
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_PRIOR_MANIFEST_INVALID"
        ) from exc
    if (
        not isinstance(previous, dict)
        or canonicalize_object(previous) != previous_raw
    ):
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_PRIOR_MANIFEST_NOT_EXACT_JCS"
        )
    validate_public_serialization(
        previous_raw,
        context.contract,
        DAILY_MANIFEST_SCHEMA,
        context.trust.expected_bundle_digest,
    )
    new_manifest_artifact = next(
        item
        for item in artifacts
        if item.relative_path == closure["manifest_path"]
    )
    new_manifest = parse_json_bytes(new_manifest_artifact.payload)
    if (
        previous.get("manifest_digest")
        != new_manifest.get("previous_manifest_digest")
        or previous.get("manifest_revision")
        != manifest_revision - 1
    ):
        raise AutoRuntimeError(
            "REPOSITORY_BINDING_PRIOR_MANIFEST_DIGEST_MISMATCH"
        )
    previous_parts = {
        int(item["part_number"]): item
        for item in previous.get("parts", [])
    }
    new_parts = {
        int(item["part_number"]): item
        for item in new_manifest.get("parts", [])
    }
    for number, deletion in deleted.items():
        prior_entry = previous_parts.get(number)
        new_entry = new_parts.get(number)
        if (
            prior_entry is None
            or prior_entry.get("state") != "ACTIVE"
            or new_entry is None
            or new_entry.get("state") != "PRUNED"
            or prior_entry.get("shard_digest")
            != deletion.prior_digest
            or prior_entry.get("shard_bytes")
            != deletion.prior_bytes
            or prior_entry.get("record_count")
            != deletion.prior_record_count
            or prior_entry.get("index_digest")
            != new_entry.get("index_digest")
            or prior_entry.get("index_bytes")
            != new_entry.get("index_bytes")
            or prior_entry.get("index_record_count")
            != new_entry.get("index_record_count")
        ):
            raise AutoRuntimeError(
                "REPOSITORY_BINDING_PRIOR_PART_NOT_EXACT"
            )
        index_path = (
            f"{local_prefix}/index-{number:04d}.jsonl"
        )
        index_raw = read_artifact(worktree, index_path)
        index_rows = validate_public_jsonl_serialization(
            index_raw,
            context.contract,
            INDEX_ENTRY_SCHEMA,
            context.trust.expected_bundle_digest,
            maximum_bytes=MAX_JSONL_BYTES,
        )
        if (
            hashlib.sha256(index_raw).hexdigest()
            != prior_entry["index_digest"]
            or len(index_raw) != prior_entry["index_bytes"]
            or len(index_rows)
            != prior_entry["index_record_count"]
        ):
            raise AutoRuntimeError(
                "REPOSITORY_BINDING_RETAINED_INDEX_MISMATCH"
            )
