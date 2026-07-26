"""Pure protected-local versus managed-raw scope gate for Task Pack M-060.

This module classifies real, non-symlink roots and candidate files, validates
the exact private ``raw-segment:v2`` contract only inside the managed staging
root, and emits public-safe observation/report bytes.  It grants scope only
for later M-061 time evaluation.  It never evaluates the 72-hour clock and
never writes, moves, truncates, chmods, or deletes any path.
"""

from __future__ import annotations

import dataclasses
import hashlib
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

_TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
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
RAW_SEGMENT_SCHEMA_ID = SCHEMA_PREFIX + "raw-segment:v2"
OBSERVATION_SCHEMA_ID = SCHEMA_PREFIX + "root-lifecycle-observation:v1"
REPORT_SCHEMA_ID = SCHEMA_PREFIX + "root-lifecycle-selection-report:v1"
OBSERVATION_SELF_POINTER = "/evidence_bundle_digest"
REPORT_SELF_POINTER = "/evidence_bundle_digest"

PROTECTED_ROOT_CLASSES = (
    "LEGACY_DATA",
    "RUN_SOURCE",
    "SKILL_SOURCE",
)
ROOT_CLASS_LIFECYCLE = {
    "LEGACY_DATA": "PROTECTED_LOCAL_DATA",
    "PUBLIC_QUEUE": "PUBLIC_SAFE_PUBLICATION_QUEUE",
    "RUN_SOURCE": "PROTECTED_LOCAL_DATA",
    "SKILL_SOURCE": "PROTECTED_LOCAL_DATA",
    "STAGING": "MANAGED_RAW_SPOOL",
}
ROOT_CLASSES = tuple(sorted(ROOT_CLASS_LIFECYCLE))
MANAGED_RAW_ROOT_CLASS = "STAGING"
PUBLIC_QUEUE_ROOT_CLASS = "PUBLIC_QUEUE"
ELIGIBLE_DECISION = "ELIGIBLE_FOR_M061_TIME_EVALUATION"
EXCLUDED_DECISION = "EXCLUDED_FROM_72H_SCOPE"
ROOT_REF_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_METADATA_BYTES = 1024 * 1024


class RootLifecycleError(ValueError):
    """A root, ownership, privacy, or lifecycle invariant failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclasses.dataclass(frozen=True)
class RootBinding:
    """Private physical root binding; ``path`` is never serialized."""

    root_ref: str
    root_class: str
    path: Path


@dataclasses.dataclass(frozen=True)
class CandidateRequest:
    """One candidate path presented to the M-060 scope gate."""

    candidate_ref: str
    metadata_path: Path


@dataclasses.dataclass(frozen=True)
class RootLifecycleResult:
    """Canonical public-safe evidence and later-M-061 candidate references."""

    canonical_observation_bytes: bytes
    observation_digest: str
    canonical_report_bytes: bytes
    report_digest: str
    selected_candidate_refs: Tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class _NormalizedRoot:
    root_ref: str
    root_class: str
    lifecycle_class: str
    lexical_path: Path
    path: Path


def _fail(code: str) -> None:
    raise RootLifecycleError(code)


def _contains(root: Path, target: Path) -> bool:
    try:
        return os.path.commonpath((str(root), str(target))) == str(root)
    except ValueError:
        return False


def _identity(value: os.stat_result) -> Tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
    )


def _normalize_root(binding: RootBinding) -> _NormalizedRoot:
    if not isinstance(binding.root_ref, str) or ROOT_REF_RE.fullmatch(
        binding.root_ref
    ) is None:
        _fail("ROOT_REF_INVALID")
    if binding.root_class not in ROOT_CLASS_LIFECYCLE:
        _fail("ROOT_CLASS_UNKNOWN")
    path = Path(binding.path)
    if not path.is_absolute():
        _fail("ROOT_PATH_MUST_BE_ABSOLUTE")
    lexical = Path(os.path.abspath(str(path)))
    try:
        info = os.lstat(str(lexical))
    except OSError as exc:
        raise RootLifecycleError("ROOT_LSTAT_FAILED") from exc
    if stat.S_ISLNK(info.st_mode):
        _fail("ROOT_SYMLINK_FORBIDDEN")
    if not stat.S_ISDIR(info.st_mode):
        _fail("ROOT_NOT_DIRECTORY")
    try:
        resolved = lexical.resolve(strict=True)
    except OSError as exc:
        raise RootLifecycleError("ROOT_REALPATH_FAILED") from exc
    return _NormalizedRoot(
        root_ref=binding.root_ref,
        root_class=binding.root_class,
        lifecycle_class=ROOT_CLASS_LIFECYCLE[binding.root_class],
        lexical_path=lexical,
        path=resolved,
    )


def _normalize_roots(
    bindings: Iterable[RootBinding],
) -> Tuple[_NormalizedRoot, ...]:
    roots = tuple(_normalize_root(binding) for binding in bindings)
    if not roots:
        _fail("ROOT_SET_EMPTY")
    refs = [root.root_ref for root in roots]
    if len(refs) != len(set(refs)):
        _fail("ROOT_REF_DUPLICATE")
    paths = [str(root.path) for root in roots]
    if len(paths) != len(set(paths)):
        _fail("ROOT_PHYSICAL_PATH_DUPLICATE")
    for index, left in enumerate(roots):
        for right in roots[index + 1 :]:
            if _contains(left.path, right.path) or _contains(
                right.path, left.path
            ):
                _fail("ROOT_OVERLAP_FORBIDDEN")
    return tuple(
        sorted(roots, key=lambda root: (-len(str(root.path)), root.root_ref))
    )


def _lexical_absolute(path: Path) -> Path:
    if not path.is_absolute():
        _fail("CANDIDATE_PATH_MUST_BE_ABSOLUTE")
    return Path(os.path.abspath(str(path)))


def _classify_candidate(
    roots: Sequence[_NormalizedRoot],
    path: Path,
    *,
    require_regular: bool = True,
) -> Tuple[_NormalizedRoot, Path, os.stat_result]:
    lexical = _lexical_absolute(path)
    matches = [
        root
        for root in roots
        if _contains(root.lexical_path, lexical)
        or _contains(root.path, lexical)
    ]
    if len(matches) != 1:
        _fail(
            "CANDIDATE_OUTSIDE_DECLARED_ROOTS"
            if not matches
            else "CANDIDATE_ROOT_AMBIGUOUS"
        )
    root = matches[0]
    try:
        base = (
            root.lexical_path
            if _contains(root.lexical_path, lexical)
            else root.path
        )
        relative = lexical.relative_to(base)
    except ValueError as exc:
        raise RootLifecycleError(
            "CANDIDATE_OUTSIDE_DECLARED_ROOTS"
        ) from exc
    if any(part in {"", ".", ".."} for part in relative.parts):
        _fail("CANDIDATE_PATH_TRAVERSAL_FORBIDDEN")
    current = base
    final_info = None
    for index, part in enumerate(relative.parts):
        current = current / part
        try:
            info = os.lstat(str(current))
        except OSError as exc:
            raise RootLifecycleError("CANDIDATE_LSTAT_FAILED") from exc
        if stat.S_ISLNK(info.st_mode):
            _fail("CANDIDATE_SYMLINK_FORBIDDEN")
        if index < len(relative.parts) - 1 and not stat.S_ISDIR(
            info.st_mode
        ):
            _fail("CANDIDATE_PARENT_NOT_DIRECTORY")
        final_info = info
    if final_info is None:
        _fail("CANDIDATE_ROOT_FILE_FORBIDDEN")
    if require_regular and not stat.S_ISREG(final_info.st_mode):
        _fail("CANDIDATE_NOT_REGULAR_FILE")
    try:
        resolved = lexical.resolve(strict=True)
    except OSError as exc:
        raise RootLifecycleError("CANDIDATE_REALPATH_FAILED") from exc
    if resolved != lexical or not _contains(root.path, resolved):
        _fail("CANDIDATE_REALPATH_ESCAPE")
    return root, resolved, final_info


def _read_regular_file(
    path: Path,
    expected: os.stat_result,
    *,
    max_bytes: Optional[int] = None,
) -> bytes:
    if stat.S_ISLNK(expected.st_mode) or not stat.S_ISREG(
        expected.st_mode
    ):
        _fail("CANDIDATE_NOT_REGULAR_FILE")
    if max_bytes is not None and expected.st_size > max_bytes:
        _fail("CANDIDATE_METADATA_TOO_LARGE")
    descriptor = None
    try:
        descriptor = os.open(
            str(path),
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
        )
        opened = os.fstat(descriptor)
        if _identity(opened) != _identity(expected):
            _fail("CANDIDATE_CHANGED_DURING_READ")
        chunks = []
        total = 0
        while True:
            block = os.read(descriptor, 1024 * 1024)
            if not block:
                break
            total += len(block)
            if max_bytes is not None and total > max_bytes:
                _fail("CANDIDATE_METADATA_TOO_LARGE")
            chunks.append(block)
        if _identity(os.lstat(str(path))) != _identity(expected):
            _fail("CANDIDATE_CHANGED_DURING_READ")
        return b"".join(chunks)
    except RootLifecycleError:
        raise
    except OSError as exc:
        raise RootLifecycleError("CANDIDATE_READ_FAILED") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def build_root_lifecycle_contract(
    candidate_bundle: ContractBundle,
    raw_segment_schema: Mapping[str, Any],
    expected_raw_segment_schema_digest: str,
    observation_schema: Mapping[str, Any],
    expected_observation_schema_digest: str,
    report_schema: Mapping[str, Any],
    expected_report_schema_digest: str,
) -> ContractBundle:
    """Add exact bundle-external raw/observation/report contracts."""

    additions = (
        (
            RAW_SEGMENT_SCHEMA_ID,
            raw_segment_schema,
            expected_raw_segment_schema_digest,
            "/segment_digest",
        ),
        (
            OBSERVATION_SCHEMA_ID,
            observation_schema,
            expected_observation_schema_digest,
            OBSERVATION_SELF_POINTER,
        ),
        (
            REPORT_SCHEMA_ID,
            report_schema,
            expected_report_schema_digest,
            REPORT_SELF_POINTER,
        ),
    )
    schemas = dict(candidate_bundle.schemas)
    pointers = dict(candidate_bundle.self_digest_pointers)
    for schema_id, document, expected_digest, pointer in additions:
        if (
            not isinstance(document, dict)
            or document.get("$id") != schema_id
            or not isinstance(expected_digest, str)
            or SHA256_RE.fullmatch(expected_digest) is None
            or canonical_digest(document) != expected_digest
        ):
            _fail("ROOT_LIFECYCLE_SCHEMA_TRUST_MISMATCH")
        if schema_id in schemas:
            _fail("ROOT_LIFECYCLE_SCHEMA_REBIND_FORBIDDEN")
        schemas[schema_id] = document
        pointers[schema_id] = pointer
    try:
        registry, format_checker = build_registry(schemas)
    except ContractError as exc:
        raise RootLifecycleError(
            "ROOT_LIFECYCLE_SCHEMA_CLOSURE_INVALID:" + str(exc)
        ) from exc
    return ContractBundle(
        schemas=schemas,
        registry=registry,
        format_checker=format_checker,
        self_digest_pointers=pointers,
        policies=candidate_bundle.policies,
        protocol_revision=candidate_bundle.protocol_revision,
    )


def raw_ownership_marker(metadata: Mapping[str, Any]) -> str:
    """Recompute the Auto-owned v2 marker without trusting a caller boolean."""

    try:
        material = {
            "domain": "SKILLOPS_MANAGED_RAW_OWNERSHIP_V1",
            "segment_uid": metadata["segment_uid"],
            "source_generation_uid": metadata["source_generation_uid"],
            "payload_digest": metadata["payload_digest"],
            "created_at": metadata["created_at"],
            "managed_owned": metadata["managed_owned"],
            "protected_or_legacy": metadata["protected_or_legacy"],
        }
    except KeyError as exc:
        raise RootLifecycleError(
            "RAW_OWNERSHIP_MARKER_INPUT_MISSING"
        ) from exc
    return hashlib.sha256(canonicalize_object(material)).hexdigest()


def _validate_managed_raw(
    bundle: ContractBundle,
    roots: Sequence[_NormalizedRoot],
    metadata_path: Path,
    metadata_info: os.stat_result,
    expected_bundle_digest: str,
) -> Mapping[str, Any]:
    metadata_raw = _read_regular_file(
        metadata_path,
        metadata_info,
        max_bytes=MAX_METADATA_BYTES,
    )
    try:
        metadata = parse_json_bytes(metadata_raw)
    except Exception as exc:
        raise RootLifecycleError("RAW_METADATA_JSON_INVALID") from exc
    if not isinstance(metadata, dict):
        _fail("RAW_METADATA_ROOT_INVALID")
    try:
        validate_instance(
            bundle,
            metadata,
            RAW_SEGMENT_SCHEMA_ID,
            expected_bundle_digest=expected_bundle_digest,
            verify_digest=True,
            public=False,
        )
    except ContractError as exc:
        raise RootLifecycleError(
            "RAW_METADATA_CONTRACT_INVALID:" + str(exc)
        ) from exc
    if metadata.get("bundle_digest") != expected_bundle_digest:
        _fail("RAW_METADATA_BUNDLE_MISMATCH")
    if metadata.get("managed_owned") is not True:
        _fail("RAW_MANAGED_OWNERSHIP_REQUIRED")
    if metadata.get("protected_or_legacy") is not False:
        _fail("RAW_PROTECTED_OR_LEGACY_FORBIDDEN")
    if metadata.get("ownership_marker_digest") != raw_ownership_marker(
        metadata
    ):
        _fail("RAW_OWNERSHIP_MARKER_INVALID")

    payload_path = metadata_path.with_suffix(".payload")
    payload_root, payload_real, payload_info = _classify_candidate(
        roots,
        payload_path,
    )
    metadata_root = next(
        root for root in roots if _contains(root.path, metadata_path)
    )
    if (
        payload_root.root_ref != metadata_root.root_ref
        or payload_root.root_class != MANAGED_RAW_ROOT_CLASS
    ):
        _fail("RAW_PAYLOAD_ROOT_MISMATCH")
    payload = _read_regular_file(payload_real, payload_info)
    if (
        len(payload) != metadata.get("byte_count")
        or hashlib.sha256(payload).hexdigest()
        != metadata.get("payload_digest")
    ):
        _fail("RAW_PAYLOAD_EVIDENCE_INVALID")
    return metadata


def _root_observation(root: _NormalizedRoot) -> Mapping[str, Any]:
    if root.lifecycle_class == "PROTECTED_LOCAL_DATA":
        ttl_selection_allowed = False
        lifecycle_action = "READ_ONLY_NO_DELETE_MOVE_TRUNCATE"
    elif root.lifecycle_class == "MANAGED_RAW_SPOOL":
        ttl_selection_allowed = True
        lifecycle_action = "M061_TIME_EVALUATION_ONLY"
    else:
        ttl_selection_allowed = False
        lifecycle_action = "RETAIN_UNTIL_REMOTE_VERIFIED"
    return {
        "root_ref": root.root_ref,
        "root_class": root.root_class,
        "lifecycle_class": root.lifecycle_class,
        "private_path_serialized": False,
        "ttl_selection_allowed": ttl_selection_allowed,
        "lifecycle_action": lifecycle_action,
    }


def _candidate_observation(
    request: CandidateRequest,
    root: _NormalizedRoot,
    *,
    decision: str,
    reason_code: str,
    metadata_read: bool,
    raw_schema_valid: bool,
    ownership_marker_verified: bool,
    payload_integrity_verified: bool,
) -> Mapping[str, Any]:
    return {
        "candidate_ref": request.candidate_ref,
        "root_ref": root.root_ref,
        "root_class": root.root_class,
        "lifecycle_class": root.lifecycle_class,
        "decision": decision,
        "reason_code": reason_code,
        "metadata_read": metadata_read,
        "raw_schema_valid": raw_schema_valid,
        "ownership_marker_verified": ownership_marker_verified,
        "payload_integrity_verified": payload_integrity_verified,
    }


def _validate_public_artifact(
    bundle: ContractBundle,
    value: Mapping[str, Any],
    schema_id: str,
    expected_bundle_digest: str,
    code: str,
) -> None:
    try:
        validate_instance(
            bundle,
            value,
            schema_id,
            expected_bundle_digest=expected_bundle_digest,
            verify_digest=True,
            public=True,
        )
    except ContractError as exc:
        raise RootLifecycleError(code + ":" + str(exc)) from exc


def _validate_observation_semantics(
    observation: Mapping[str, Any],
) -> None:
    roots = observation["root_bindings"]
    if [row["root_ref"] for row in roots] != sorted(
        row["root_ref"] for row in roots
    ):
        _fail("ROOT_LIFECYCLE_ROOT_ORDER_INVALID")
    by_ref: Dict[str, Mapping[str, Any]] = {}
    for row in roots:
        root_ref = row["root_ref"]
        if root_ref in by_ref:
            _fail("ROOT_LIFECYCLE_ROOT_REF_DUPLICATE")
        root_class = row["root_class"]
        lifecycle = ROOT_CLASS_LIFECYCLE.get(root_class)
        if lifecycle is None or row["lifecycle_class"] != lifecycle:
            _fail("ROOT_LIFECYCLE_CLASS_MAPPING_MISMATCH")
        if lifecycle == "PROTECTED_LOCAL_DATA":
            expected_ttl = False
            expected_action = "READ_ONLY_NO_DELETE_MOVE_TRUNCATE"
        elif lifecycle == "MANAGED_RAW_SPOOL":
            expected_ttl = True
            expected_action = "M061_TIME_EVALUATION_ONLY"
        else:
            expected_ttl = False
            expected_action = "RETAIN_UNTIL_REMOTE_VERIFIED"
        if (
            row["private_path_serialized"] is not False
            or row["ttl_selection_allowed"] is not expected_ttl
            or row["lifecycle_action"] != expected_action
        ):
            _fail("ROOT_LIFECYCLE_ROOT_POLICY_MISMATCH")
        by_ref[root_ref] = row

    evaluations = observation["candidate_evaluations"]
    refs = [row["candidate_ref"] for row in evaluations]
    if refs != sorted(refs) or len(refs) != len(set(refs)):
        _fail("ROOT_LIFECYCLE_CANDIDATE_ORDER_OR_DUPLICATE")
    for row in evaluations:
        root = by_ref.get(row["root_ref"])
        if root is None:
            _fail("ROOT_LIFECYCLE_CANDIDATE_ROOT_UNKNOWN")
        if (
            row["root_class"] != root["root_class"]
            or row["lifecycle_class"] != root["lifecycle_class"]
        ):
            _fail("ROOT_LIFECYCLE_CANDIDATE_ROOT_MISMATCH")
        lifecycle = row["lifecycle_class"]
        evidence_flags = (
            row["metadata_read"],
            row["raw_schema_valid"],
            row["ownership_marker_verified"],
            row["payload_integrity_verified"],
        )
        if lifecycle == "PROTECTED_LOCAL_DATA":
            if (
                row["decision"] != EXCLUDED_DECISION
                or row["reason_code"] != "PROTECTED_LOCAL_TTL_FORBIDDEN"
                or evidence_flags != (False, False, False, False)
            ):
                _fail("PROTECTED_LOCAL_SELECTION_SEMANTICS_INVALID")
        elif lifecycle == "PUBLIC_SAFE_PUBLICATION_QUEUE":
            if (
                row["decision"] != EXCLUDED_DECISION
                or row["reason_code"]
                != "PUBLIC_SAFE_QUEUE_NOT_RAW_SPOOL"
                or evidence_flags != (False, False, False, False)
            ):
                _fail("PUBLIC_QUEUE_SELECTION_SEMANTICS_INVALID")
        elif lifecycle == "MANAGED_RAW_SPOOL":
            if evidence_flags != (True, True, True, True):
                _fail("MANAGED_RAW_EVIDENCE_CLOSURE_INCOMPLETE")
            if row["decision"] == ELIGIBLE_DECISION:
                if row["reason_code"] != ELIGIBLE_DECISION:
                    _fail("MANAGED_RAW_ELIGIBLE_REASON_INVALID")
            elif row["reason_code"] not in {
                "PERSISTENCE_DISABLED",
                "TEST_ONLY_NOT_AUTHORIZED",
            }:
                _fail("MANAGED_RAW_EXCLUSION_REASON_INVALID")
        else:
            _fail("ROOT_LIFECYCLE_CLASS_UNKNOWN")


def recompute_selection_report(
    bundle: ContractBundle,
    observation: Mapping[str, Any],
    *,
    report_uid: str,
    expected_bundle_digest: str,
) -> Mapping[str, Any]:
    """Recompute the report from a schema/digest-valid observation."""

    if not isinstance(observation, dict):
        _fail("ROOT_LIFECYCLE_OBSERVATION_ROOT_INVALID")
    _validate_public_artifact(
        bundle,
        observation,
        OBSERVATION_SCHEMA_ID,
        expected_bundle_digest,
        "ROOT_LIFECYCLE_OBSERVATION_INVALID",
    )
    _validate_observation_semantics(observation)
    evaluations = observation["candidate_evaluations"]
    selected = sorted(
        row["candidate_ref"]
        for row in evaluations
        if row["decision"] == ELIGIBLE_DECISION
    )
    excluded = sorted(
        (
            {
                "candidate_ref": row["candidate_ref"],
                "reason_code": row["reason_code"],
            }
            for row in evaluations
            if row["decision"] == EXCLUDED_DECISION
        ),
        key=lambda row: row["candidate_ref"],
    )
    protected = [
        row
        for row in evaluations
        if row["root_class"] in PROTECTED_ROOT_CLASSES
    ]
    legacy = [
        row for row in evaluations if row["root_class"] == "LEGACY_DATA"
    ]
    public_queue = [
        row for row in evaluations if row["root_class"] == PUBLIC_QUEUE_ROOT_CLASS
    ]
    protected_selected = [
        row for row in protected if row["decision"] == ELIGIBLE_DECISION
    ]
    legacy_selected = [
        row for row in legacy if row["decision"] == ELIGIBLE_DECISION
    ]
    public_queue_selected = [
        row for row in public_queue if row["decision"] == ELIGIBLE_DECISION
    ]
    if protected_selected or legacy_selected or public_queue_selected:
        _fail("PROTECTED_OR_QUEUE_CANDIDATE_SELECTED")
    report: Dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": expected_bundle_digest,
        "report_uid": report_uid,
        "observation_ref": {
            "artifact_digest": observation["evidence_bundle_digest"],
        },
        "selection_state": "PASS",
        "scope_authorization": "M061_TIME_EVALUATION_ONLY",
        "selected_candidate_refs": selected,
        "excluded_candidates": excluded,
        "root_count": len(observation["root_bindings"]),
        "input_count": len(evaluations),
        "selected_count": len(selected),
        "protected_input_count": len(protected),
        "legacy_input_count": len(legacy),
        "public_queue_input_count": len(public_queue),
        "protected_selected_count": 0,
        "legacy_selected_count": 0,
        "public_queue_selected_count": 0,
        "protected_delete_budget": 0,
        "time_evaluation_performed": False,
        "destructive_action_performed": False,
        "public_artifact_write_performed": False,
        "generated_at": observation["observed_at"],
        "actor": "SKILLOPS_ROOT_LIFECYCLE_GUARD",
        "evidence_bundle_digest": "0" * 64,
    }
    report["evidence_bundle_digest"] = canonical_digest(
        report,
        REPORT_SELF_POINTER,
    )
    _validate_public_artifact(
        bundle,
        report,
        REPORT_SCHEMA_ID,
        expected_bundle_digest,
        "ROOT_LIFECYCLE_REPORT_INVALID",
    )
    return report


def validate_selection_report(
    bundle: ContractBundle,
    observation: Mapping[str, Any],
    report: Mapping[str, Any],
    *,
    expected_bundle_digest: str,
) -> None:
    """Reject a supplied report unless it equals deterministic recomputation."""

    if not isinstance(report, dict):
        _fail("ROOT_LIFECYCLE_REPORT_ROOT_INVALID")
    expected = recompute_selection_report(
        bundle,
        observation,
        report_uid=report.get("report_uid", ""),
        expected_bundle_digest=expected_bundle_digest,
    )
    if canonicalize_object(expected) != canonicalize_object(report):
        _fail("ROOT_LIFECYCLE_REPORT_RECOMPUTATION_MISMATCH")


def evaluate_retention_scope(
    bundle: ContractBundle,
    *,
    root_bindings: Sequence[RootBinding],
    candidates: Sequence[CandidateRequest],
    observation_uid: str,
    report_uid: str,
    observed_at: str,
    expected_bundle_digest: str,
    allow_test_only: bool = False,
) -> RootLifecycleResult:
    """Classify scope without performing time evaluation or any mutation."""

    roots = _normalize_roots(root_bindings)
    requests = tuple(candidates)
    refs = [request.candidate_ref for request in requests]
    if any(ROOT_REF_RE.fullmatch(ref) is None for ref in refs):
        _fail("CANDIDATE_REF_INVALID")
    if len(refs) != len(set(refs)):
        _fail("CANDIDATE_REF_DUPLICATE")

    evaluations = []
    for request in sorted(requests, key=lambda item: item.candidate_ref):
        root, metadata_path, metadata_info = _classify_candidate(
            roots,
            Path(request.metadata_path),
        )
        if root.lifecycle_class == "PROTECTED_LOCAL_DATA":
            evaluations.append(
                _candidate_observation(
                    request,
                    root,
                    decision=EXCLUDED_DECISION,
                    reason_code="PROTECTED_LOCAL_TTL_FORBIDDEN",
                    metadata_read=False,
                    raw_schema_valid=False,
                    ownership_marker_verified=False,
                    payload_integrity_verified=False,
                )
            )
            continue
        if root.lifecycle_class == "PUBLIC_SAFE_PUBLICATION_QUEUE":
            evaluations.append(
                _candidate_observation(
                    request,
                    root,
                    decision=EXCLUDED_DECISION,
                    reason_code="PUBLIC_SAFE_QUEUE_NOT_RAW_SPOOL",
                    metadata_read=False,
                    raw_schema_valid=False,
                    ownership_marker_verified=False,
                    payload_integrity_verified=False,
                )
            )
            continue
        if root.root_class != MANAGED_RAW_ROOT_CLASS:
            _fail("MANAGED_RAW_ROOT_CLASS_MISMATCH")
        metadata = _validate_managed_raw(
            bundle,
            roots,
            metadata_path,
            metadata_info,
            expected_bundle_digest,
        )
        mode = metadata["persistence_mode"]
        if mode == "DISABLED":
            decision = EXCLUDED_DECISION
            reason_code = "PERSISTENCE_DISABLED"
        elif mode == "TEST_ONLY" and not allow_test_only:
            decision = EXCLUDED_DECISION
            reason_code = "TEST_ONLY_NOT_AUTHORIZED"
        elif mode == "TEST_ONLY":
            decision = ELIGIBLE_DECISION
            reason_code = ELIGIBLE_DECISION
        elif mode == "ENABLED_AFTER_CERTIFICATION":
            _fail("MANAGED_RAW_CERTIFICATION_NOT_IMPLEMENTED_M060")
        else:
            _fail("RAW_PERSISTENCE_MODE_UNKNOWN")
        evaluations.append(
            _candidate_observation(
                request,
                root,
                decision=decision,
                reason_code=reason_code,
                metadata_read=True,
                raw_schema_valid=True,
                ownership_marker_verified=True,
                payload_integrity_verified=True,
            )
        )

    observation: Dict[str, Any] = {
        "schema_version": OBSERVATION_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": expected_bundle_digest,
        "observation_uid": observation_uid,
        "observed_at": observed_at,
        "root_bindings": [
            _root_observation(root)
            for root in sorted(roots, key=lambda item: item.root_ref)
        ],
        "candidate_evaluations": evaluations,
        "persistent_managed_raw_default_enabled": False,
        "ttl_enforcement_availability": "LOCAL_RUNTIME_AVAILABLE_ONLY",
        "offline_period_hard_guarantee_claimed": False,
        "offline_resume_first_cycle_receipt_required": True,
        "offline_gap_receipt_required": True,
        "time_evaluation_performed": False,
        "destructive_action_performed": False,
        "actor": "SKILLOPS_ROOT_LIFECYCLE_GUARD",
        "evidence_bundle_digest": "0" * 64,
    }
    observation["evidence_bundle_digest"] = canonical_digest(
        observation,
        OBSERVATION_SELF_POINTER,
    )
    _validate_public_artifact(
        bundle,
        observation,
        OBSERVATION_SCHEMA_ID,
        expected_bundle_digest,
        "ROOT_LIFECYCLE_OBSERVATION_INVALID",
    )
    report = recompute_selection_report(
        bundle,
        observation,
        report_uid=report_uid,
        expected_bundle_digest=expected_bundle_digest,
    )
    selected = tuple(report["selected_candidate_refs"])
    return RootLifecycleResult(
        canonical_observation_bytes=canonicalize_object(observation),
        observation_digest=observation["evidence_bundle_digest"],
        canonical_report_bytes=canonicalize_object(report),
        report_digest=report["evidence_bundle_digest"],
        selected_candidate_refs=selected,
    )
