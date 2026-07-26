"""Externally trusted dual-read consumer for version-policy v2 and v3.

The v2 policy remains the exact candidate member.  The v3 policy remains a
bundle-external shadow draft.  A caller must select one policy and its matching
read mode explicitly; this module never merges policy objects and never grants
release, schedule, notification, or runtime-write authority.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence, Tuple

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

GOVERNANCE_TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(GOVERNANCE_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(GOVERNANCE_TOOLS_DIR))

from CodexSkills.governance.release.foundations import (
    MATERIAL_TRIGGER_CODES,
    ROUTINE_TRIGGER_CODES,
)
from CodexSkills.governance.release.version_policy_v3.contract import (
    PROTOCOL_REVISION,
    SCHEDULE_CANDIDATES,
    UNRESOLVED_SCHEDULE_CODE,
    VERSION_POLICY_V2_ID,
    VERSION_POLICY_V3_ID,
    VersionPolicyV3Error,
    classify_v3_impact,
    validate_v2_to_v3_compatibility,
)
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_mechanism import (
    ContractBundle,
    TrustTuple,
    load_trusted_bundle,
)


VERSION_POLICY_CONSUMER_READINESS_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:version-policy-consumer-readiness:v1"
)
DRAFT_INTERFACE_PATH = (
    "CodexSkills/governance/release/version_policy_v3/"
    "draft-interface.json"
)
DRAFT_INTERFACE_MODE = "DRAFT_NON_ACTIVE_VERSION_POLICY"
CANDIDATE_MANIFEST_PATH = (
    "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
)
PREDECESSOR_SELECTION_MODE = "PREDECESSOR_READ_ONLY"
SUCCESSOR_SELECTION_MODE = "SUCCESSOR_SHADOW"

GIT_OBJECT_RE = re.compile(
    r"^(?:(sha1):([0-9a-f]{40})|(sha256):([0-9a-f]{64}))$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class VersionPolicyConsumerError(ValueError):
    """A dual-read trust or selection invariant failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class VersionPolicyDraftTrustTuple:
    verified_git_object_id: str
    expected_interface_raw_sha256: str
    canonical_interface_path: str
    mode: str


@dataclass(frozen=True)
class TrustedVersionPolicySet:
    predecessor: Mapping[str, Any]
    successor: Mapping[str, Any]
    notification_policy: Mapping[str, Any]
    candidate_bundle: ContractBundle
    compatibility: Mapping[str, Any]
    candidate_manifest_raw_sha256: str
    draft_interface_raw_sha256: str


def _run_git(repo_root: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_GIT_UNAVAILABLE"
        ) from exc
    if result.returncode != 0:
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_GIT_COMMAND_FAILED"
        )
    return result.stdout


def _split_git_object(repo_root: Path, tagged: str, code: str) -> str:
    match = GIT_OBJECT_RE.fullmatch(tagged)
    if not match:
        raise VersionPolicyConsumerError(code + "_GIT_OBJECT_INVALID")
    algorithm = match.group(1) or match.group(3)
    object_id = match.group(2) or match.group(4)
    observed = _run_git(
        repo_root,
        "rev-parse",
        "--show-object-format",
    ).decode("ascii", errors="strict").strip()
    if observed != algorithm:
        raise VersionPolicyConsumerError(code + "_GIT_ALGORITHM_MISMATCH")
    _run_git(repo_root, "cat-file", "-e", object_id + "^{commit}")
    return object_id


def _git_blob(repo_root: Path, object_id: str, relative_path: str) -> bytes:
    return _run_git(repo_root, "show", object_id + ":" + relative_path)


def _object(raw: bytes, code: str) -> Mapping[str, Any]:
    try:
        value = parse_json_bytes(raw)
    except Exception as exc:
        raise VersionPolicyConsumerError(code + "_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise VersionPolicyConsumerError(code + "_ROOT_INVALID")
    return value


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_sha(value: Mapping[str, Any]) -> str:
    return _sha256(canonicalize_object(value))


def _validate_policy_schema(
    common_schema: Mapping[str, Any],
    policy_schema: Mapping[str, Any],
    policy: Mapping[str, Any],
    code: str,
) -> None:
    try:
        Draft202012Validator.check_schema(policy_schema)
        registry = Registry().with_resources(
            (
                (common_schema["$id"], Resource.from_contents(common_schema)),
                (policy_schema["$id"], Resource.from_contents(policy_schema)),
            )
        )
        errors = sorted(
            Draft202012Validator(
                policy_schema,
                registry=registry,
            ).iter_errors(policy),
            key=lambda item: tuple(str(piece) for piece in item.absolute_path),
        )
    except Exception as exc:
        raise VersionPolicyConsumerError(code + "_SCHEMA_CLOSURE_INVALID") from exc
    if errors:
        raise VersionPolicyConsumerError(code + "_SCHEMA_VALIDATION_FAILED")


def load_trusted_version_policies(
    repo_root: Path,
    candidate_trust: TrustTuple,
    expected_candidate_manifest_raw_sha256: str,
    draft_trust: VersionPolicyDraftTrustTuple,
) -> TrustedVersionPolicySet:
    """Load exact v2 candidate and v3 shadow bytes from independent Git roots."""

    root = repo_root.resolve(strict=True)
    if (
        candidate_trust.canonical_manifest_path != CANDIDATE_MANIFEST_PATH
        or candidate_trust.mode != "CANDIDATE"
        or not SHA256_RE.fullmatch(expected_candidate_manifest_raw_sha256)
    ):
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_CANDIDATE_TRUST_INVALID"
        )
    candidate_object = _split_git_object(
        root,
        candidate_trust.verified_git_object_id,
        "VERSION_POLICY_CONSUMER_CANDIDATE",
    )
    candidate_manifest_raw = _git_blob(
        root,
        candidate_object,
        candidate_trust.canonical_manifest_path,
    )
    if _sha256(candidate_manifest_raw) != expected_candidate_manifest_raw_sha256:
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_CANDIDATE_MANIFEST_RAW_MISMATCH"
        )
    candidate_bundle = load_trusted_bundle(root, candidate_trust)
    try:
        predecessor = candidate_bundle.policies[VERSION_POLICY_V2_ID]
        notification_policy = candidate_bundle.policies[
            "urn:linzecolin:agentdatabase:skillops:policy:notification:v1"
        ]
    except KeyError as exc:
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_CANDIDATE_POLICY_MISSING"
        ) from exc

    if (
        draft_trust.canonical_interface_path != DRAFT_INTERFACE_PATH
        or draft_trust.mode != DRAFT_INTERFACE_MODE
        or not SHA256_RE.fullmatch(
            draft_trust.expected_interface_raw_sha256
        )
    ):
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_DRAFT_TRUST_INVALID"
        )
    draft_object = _split_git_object(
        root,
        draft_trust.verified_git_object_id,
        "VERSION_POLICY_CONSUMER_DRAFT",
    )
    draft_interface_raw = _git_blob(
        root,
        draft_object,
        draft_trust.canonical_interface_path,
    )
    if _sha256(draft_interface_raw) != draft_trust.expected_interface_raw_sha256:
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_DRAFT_INTERFACE_RAW_MISMATCH"
        )
    draft_interface = _object(
        draft_interface_raw,
        "VERSION_POLICY_CONSUMER_DRAFT_INTERFACE",
    )
    if (
        draft_interface.get("schema_version")
        != (
            "urn:linzecolin:agentdatabase:skillops:"
            "schema:version-policy-draft-interface:v1"
        )
        or draft_interface.get("protocol_revision") != PROTOCOL_REVISION
        or draft_interface.get("status")
        != "DRAFT_NON_ACTIVE_CONSUMER_FIRST_REQUIRED"
        or draft_interface.get("artifact_digest")
        != canonical_digest(draft_interface, "/artifact_digest")
        or draft_interface.get("draft_trust_contract", {}).get(
            "expected_mode"
        )
        != DRAFT_INTERFACE_MODE
        or draft_interface.get("candidate_bundle", {}).get("bundle_digest")
        != candidate_trust.expected_bundle_digest
        or draft_interface.get("candidate_bundle", {}).get("schema_count")
        != 31
        or draft_interface.get("candidate_bundle", {}).get("policy_count")
        != 5
        or draft_interface.get("candidate_bundle", {}).get(
            "v3_schema_member"
        )
        is not False
        or draft_interface.get("candidate_bundle", {}).get(
            "v3_policy_member"
        )
        is not False
    ):
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_DRAFT_INTERFACE_CONTRACT_MISMATCH"
        )

    draft_descriptor = draft_interface.get("draft")
    predecessor_descriptor = draft_interface.get("predecessor")
    notification_descriptor = draft_interface.get("notification_policy")
    if not all(
        isinstance(value, dict)
        for value in (
            draft_descriptor,
            predecessor_descriptor,
            notification_descriptor,
        )
    ):
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_DRAFT_DESCRIPTOR_INVALID"
        )

    v3_schema_raw = _git_blob(
        root,
        draft_object,
        draft_descriptor["schema_path"],
    )
    v3_policy_raw = _git_blob(
        root,
        draft_object,
        draft_descriptor["policy_path"],
    )
    v3_schema = _object(
        v3_schema_raw,
        "VERSION_POLICY_CONSUMER_V3_SCHEMA",
    )
    successor = _object(
        v3_policy_raw,
        "VERSION_POLICY_CONSUMER_V3_POLICY",
    )
    if (
        _canonical_sha(v3_schema) != draft_descriptor["schema_sha256"]
        or _canonical_sha(successor) != draft_descriptor["policy_sha256"]
    ):
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_V3_DESCRIPTOR_DIGEST_MISMATCH"
        )

    predecessor_policy_raw = _git_blob(
        root,
        candidate_object,
        predecessor_descriptor["policy_path"],
    )
    predecessor_schema_raw = _git_blob(
        root,
        candidate_object,
        predecessor_descriptor["schema_path"],
    )
    notification_raw = _git_blob(
        root,
        candidate_object,
        notification_descriptor["relative_path"],
    )
    if (
        predecessor_policy_raw
        != _git_blob(
            root,
            draft_object,
            predecessor_descriptor["policy_path"],
        )
        or predecessor_schema_raw
        != _git_blob(
            root,
            draft_object,
            predecessor_descriptor["schema_path"],
        )
        or notification_raw
        != _git_blob(
            root,
            draft_object,
            notification_descriptor["relative_path"],
        )
        or _canonical_sha(predecessor)
        != predecessor_descriptor["policy_sha256"]
        or _canonical_sha(
            _object(
                predecessor_schema_raw,
                "VERSION_POLICY_CONSUMER_V2_SCHEMA",
            )
        )
        != predecessor_descriptor["schema_sha256"]
        or _canonical_sha(notification_policy)
        != notification_descriptor["policy_sha256"]
    ):
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_PREDECESSOR_BYTE_DRIFT"
        )

    common_path = (
        "CodexSkills/governance/schemas/common-definitions.schema.json"
    )
    common_raw = _git_blob(root, candidate_object, common_path)
    if common_raw != _git_blob(root, draft_object, common_path):
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_COMMON_SCHEMA_DRIFT"
        )
    common_schema = _object(
        common_raw,
        "VERSION_POLICY_CONSUMER_COMMON_SCHEMA",
    )
    predecessor_schema = _object(
        predecessor_schema_raw,
        "VERSION_POLICY_CONSUMER_V2_SCHEMA",
    )
    _validate_policy_schema(
        common_schema,
        predecessor_schema,
        predecessor,
        "VERSION_POLICY_CONSUMER_V2",
    )
    _validate_policy_schema(
        common_schema,
        v3_schema,
        successor,
        "VERSION_POLICY_CONSUMER_V3",
    )
    try:
        compatibility = validate_v2_to_v3_compatibility(
            predecessor,
            successor,
            notification_policy,
        )
    except VersionPolicyV3Error as exc:
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_COMPATIBILITY_INVALID:" + exc.code
        ) from exc
    return TrustedVersionPolicySet(
        predecessor=predecessor,
        successor=successor,
        notification_policy=notification_policy,
        candidate_bundle=candidate_bundle,
        compatibility=compatibility,
        candidate_manifest_raw_sha256=_sha256(candidate_manifest_raw),
        draft_interface_raw_sha256=_sha256(draft_interface_raw),
    )


def _selected_policy(
    trusted: TrustedVersionPolicySet,
    policy_id: str,
    selection_mode: str,
) -> Mapping[str, Any]:
    expected = {
        VERSION_POLICY_V2_ID: (
            PREDECESSOR_SELECTION_MODE,
            trusted.predecessor,
        ),
        VERSION_POLICY_V3_ID: (
            SUCCESSOR_SELECTION_MODE,
            trusted.successor,
        ),
    }
    if policy_id not in expected:
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_POLICY_ID_UNSUPPORTED"
        )
    expected_mode, policy = expected[policy_id]
    if selection_mode != expected_mode:
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_SELECTION_MODE_MISMATCH"
        )
    return policy


def classify_policy_impact(
    trusted: TrustedVersionPolicySet,
    *,
    policy_id: str,
    selection_mode: str,
    trigger_codes: Sequence[str],
) -> str:
    """Classify with one explicit policy; hybrid or implicit selection stops."""

    policy = _selected_policy(trusted, policy_id, selection_mode)
    if (
        not isinstance(trigger_codes, (list, tuple))
        or not trigger_codes
        or any(not isinstance(code, str) for code in trigger_codes)
    ):
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_TRIGGER_INPUT_INVALID"
        )
    normalized: Tuple[str, ...] = tuple(sorted(trigger_codes))
    if len(set(normalized)) != len(normalized):
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_TRIGGER_DUPLICATE"
        )
    if policy_id == VERSION_POLICY_V3_ID:
        try:
            return classify_v3_impact(normalized, policy)
        except VersionPolicyV3Error as exc:
            raise VersionPolicyConsumerError(
                "VERSION_POLICY_CONSUMER_TRIGGER_UNKNOWN"
            ) from exc

    predecessor_major = set(policy["major_trigger_codes"])
    known = (
        set(ROUTINE_TRIGGER_CODES)
        | set(MATERIAL_TRIGGER_CODES)
        | predecessor_major
    )
    unsupported = set(normalized).intersection(
        set(trusted.successor["major_trigger_codes"]) - predecessor_major
    )
    if unsupported:
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_PREDECESSOR_TRIGGER_UNSUPPORTED"
        )
    if set(normalized).difference(known):
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_TRIGGER_UNKNOWN"
        )
    if set(normalized).intersection(predecessor_major):
        return "MAJOR"
    if set(normalized).intersection(MATERIAL_TRIGGER_CODES):
        return "MINOR"
    return "PATCH"


def read_schedule_contract(
    trusted: TrustedVersionPolicySet,
    *,
    policy_id: str,
    selection_mode: str,
) -> Mapping[str, Any]:
    """Expose observed policy data while keeping authority unresolved."""

    policy = _selected_policy(trusted, policy_id, selection_mode)
    observed = policy["daily_schedule_local"]
    return {
        "policy_id": policy_id,
        "selection_mode": selection_mode,
        "timezone": "Australia/Sydney",
        "observed_daily_schedule_local": observed,
        "daily_schedule_candidate_local_times": list(SCHEDULE_CANDIDATES),
        "daily_schedule_authority_state": "UNRESOLVED",
        "schedule_conflict_code": UNRESOLVED_SCHEDULE_CODE,
        "schedule_activation_permitted": False,
    }


def assert_schedule_activation_permitted(
    trusted: TrustedVersionPolicySet,
    *,
    policy_id: str,
    selection_mode: str,
) -> None:
    contract = read_schedule_contract(
        trusted,
        policy_id=policy_id,
        selection_mode=selection_mode,
    )
    if contract["schedule_activation_permitted"] is not True:
        raise VersionPolicyConsumerError(
            "VERSION_POLICY_CONSUMER_SCHEDULE_AUTHORITY_UNRESOLVED"
        )
