#!/usr/bin/env python3
"""Build and validate the non-active M0 release-foundation interface."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from CodexSkills.governance.release.foundations import (  # noqa: E402
    FOUNDATION_INTERFACE_SCHEMA_ID,
    IMPACT_TRANSLATION,
    LOCKED_MAJOR_TRIGGER_CODES,
    PROTOCOL_REVISION,
    PolicyClaim,
    detect_policy_conflicts,
    validate_version_policy,
)
from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
)


GOVERNANCE_DIR = REPO_ROOT / "CodexSkills" / "governance"
RELEASE_DIR = GOVERNANCE_DIR / "release"
SCHEMA_DIR = RELEASE_DIR / "schemas"
INTERFACE_PATH = RELEASE_DIR / "foundation-interface.json"
COMMON_SCHEMA_PATH = GOVERNANCE_DIR / "schemas" / "common-definitions.schema.json"
VERSION_POLICY_PATH = GOVERNANCE_DIR / "policies" / "version-policy.v2.json"
CANDIDATE_MANIFEST_PATH = (
    GOVERNANCE_DIR / "bundles" / "schema-bundle-manifest.v1.json"
)
CONTROL_INTERFACE_PATH = (
    GOVERNANCE_DIR / "activation" / "control-interface.json"
)
ACTIVE_VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

TASK_PACK_REVISION = "v0.0.0.2"
TASK_PACK_PROVENANCE = (
    (
        "CHECKSUM_MANIFEST",
        "ac931ae956ecc115fa051550b1b5d652c6cf4212a8f831bc35d2c8c177f81e00",
    ),
    (
        "MECHANISM_TASK_GRAPH",
        "0d383361187186690583684b702bbff934455e1b6782916bfee31baac2a87b06",
    ),
    (
        "OWNER_DECISIONS",
        "b1bfe37f8ceb57b49a44ccc284b790b6ad6eb0155d054ffc07b44a928a237dc1",
    ),
    (
        "POLICY_PRECEDENCE",
        "bfba0de7b78978d220338f7e88f8889b3895abefd78b2d3561d60c5342f3b987",
    ),
    (
        "VERSION_NOTIFICATION_POLICY",
        "dfc66399a12c2e63abab437bdf9f788f645ea460590cd3eceead7046b6a1a45c",
    ),
)
SCHEMA_PATHS = (
    (
        "urn:linzecolin:agentdatabase:skillops:"
        "schema:release-foundation-interface:v1",
        "CodexSkills/governance/release/schemas/"
        "release-foundation-interface.schema.json",
        "/artifact_digest",
    ),
    (
        "urn:linzecolin:agentdatabase:skillops:schema:release-handoff:v1",
        "CodexSkills/governance/release/schemas/release-handoff.schema.json",
        "/artifact_digest",
    ),
    (
        "urn:linzecolin:agentdatabase:skillops:"
        "schema:revision-allocation-ledger:v1",
        "CodexSkills/governance/release/schemas/"
        "revision-allocation-ledger.schema.json",
        "/ledger_digest",
    ),
)
M0_TASK_STATUSES = (
    ("M-004", "IMPLEMENTED"),
    ("M-005", "SEMANTIC_CONTRACT_IMPLEMENTED_EXECUTOR_PENDING"),
    ("M-006", "IMPLEMENTED_POLICY_RECONCILIATION_REQUIRED"),
    ("M-008", "IMPLEMENTED"),
    ("M-009", "IMPLEMENTED"),
)
NEXT_PHASE = "MECHANISM_VERSION_POLICY_V3_DRAFT"


class FoundationBuildError(ValueError):
    """The foundation interface cannot be reproduced exactly."""


def _strict_json(path: Path) -> Mapping[str, Any]:
    try:
        value = parse_json_bytes(path.read_bytes())
    except Exception as exc:
        raise FoundationBuildError(
            "FOUNDATION_JSON_INVALID:" + path.as_posix()
        ) from exc
    if not isinstance(value, dict):
        raise FoundationBuildError(
            "FOUNDATION_JSON_ROOT_INVALID:" + path.as_posix()
        )
    return value


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _schema_entries() -> Sequence[Mapping[str, str]]:
    rows = []
    for schema_id, relative_path, self_digest_pointer in SCHEMA_PATHS:
        path = REPO_ROOT.joinpath(*relative_path.split("/"))
        document = _strict_json(path)
        if document.get("$id") != schema_id:
            raise FoundationBuildError(
                "FOUNDATION_SCHEMA_ID_MISMATCH:" + schema_id
            )
        rows.append(
            {
                "id": schema_id,
                "relative_path": relative_path,
                "schema_sha256": _sha256(canonicalize_object(document)),
                "self_digest_pointer": self_digest_pointer,
            }
        )
    return sorted(rows, key=lambda row: row["id"].encode("ascii"))


def _policy_conflicts(
    policy: Mapping[str, Any],
) -> Sequence[Mapping[str, Any]]:
    return list(
        detect_policy_conflicts(
            [
                PolicyClaim(
                    "/version/major_trigger_codes",
                    "OWNER_LOCK",
                    "TASKPACK_06_VERSION_NOTIFICATION_POLICY",
                    sorted(LOCKED_MAJOR_TRIGGER_CODES),
                ),
                PolicyClaim(
                    "/version/major_trigger_codes",
                    "VALIDATED_CONFIG",
                    "VERSION_POLICY_V2",
                    policy["major_trigger_codes"],
                ),
            ]
        )
    )


def build_interface() -> Mapping[str, Any]:
    policy = _strict_json(VERSION_POLICY_PATH)
    candidate = _strict_json(CANDIDATE_MANIFEST_PATH)
    control_raw = CONTROL_INTERFACE_PATH.read_bytes()
    missing = validate_version_policy(policy)
    conflicts = _policy_conflicts(policy)
    if not missing or not conflicts:
        raise FoundationBuildError(
            "FOUNDATION_EXPECTED_POLICY_RECONCILIATION_MISSING"
        )
    interface: Dict[str, Any] = {
        "schema_version": FOUNDATION_INTERFACE_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "status": "DRAFT_NON_ACTIVE_POLICY_RECONCILIATION_REQUIRED",
        "task_pack_revision": TASK_PACK_REVISION,
        "task_pack_provenance": [
            {
                "artifact_code": artifact_code,
                "digest_basis": "RAW_BYTES",
                "artifact_digest": digest,
            }
            for artifact_code, digest in TASK_PACK_PROVENANCE
        ],
        "bundle_digest": candidate["bundle_digest"],
        "candidate_bundle_unchanged": True,
        "control_interface": {
            "relative_path": (
                "CodexSkills/governance/activation/control-interface.json"
            ),
            "digest_basis": "RAW_BYTES",
            "artifact_digest": _sha256(control_raw),
        },
        "control_interface_unchanged": True,
        "foundation_schemas": list(_schema_entries()),
        "version_policy": {
            "policy_id": policy["policy_id"],
            "policy_sha256": _sha256(
                canonicalize_object(policy)
            ),
            "impact_translation": dict(IMPACT_TRANSLATION),
            "major_trigger_coverage_complete": False,
            "missing_major_trigger_codes": list(missing),
        },
        "policy_conflicts": conflicts,
        "m0_task_statuses": [
            {"task_id": task_id, "status": status}
            for task_id, status in M0_TASK_STATUSES
        ],
        "schedule_authority_resolved": False,
        "release_write_permitted": False,
        "activation_forbidden": True,
        "next_phase": NEXT_PHASE,
        "artifact_digest": "0" * 64,
    }
    interface["artifact_digest"] = canonical_digest(
        interface,
        "/artifact_digest",
    )
    return interface


def render_interface() -> bytes:
    return (
        json.dumps(
            build_interface(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def validate_interface(interface: Mapping[str, Any]) -> None:
    expected = build_interface()
    if interface != expected:
        raise FoundationBuildError(
            "FOUNDATION_INTERFACE_SEMANTIC_DRIFT"
        )
    if interface["artifact_digest"] != canonical_digest(
        interface,
        "/artifact_digest",
    ):
        raise FoundationBuildError(
            "FOUNDATION_INTERFACE_DIGEST_MISMATCH"
        )
    if ACTIVE_VERSION_PATH.exists():
        raise FoundationBuildError(
            "FOUNDATION_ACTIVE_VERSION_FORBIDDEN"
        )
    candidate_ids = {
        row["id"]
        for row in _strict_json(CANDIDATE_MANIFEST_PATH)["schemas"]
    }
    foundation_ids = {
        row["id"] for row in interface["foundation_schemas"]
    }
    if candidate_ids.intersection(foundation_ids):
        raise FoundationBuildError(
            "FOUNDATION_SCHEMA_PREMATURE_CANDIDATE_MEMBERSHIP"
        )
    if _strict_json(COMMON_SCHEMA_PATH).get("$id") != (
        "urn:linzecolin:agentdatabase:skillops:"
        "schema:common-definitions:v1"
    ):
        raise FoundationBuildError(
            "FOUNDATION_COMMON_SCHEMA_MISMATCH"
        )


def _check() -> None:
    expected_raw = render_interface()
    try:
        actual_raw = INTERFACE_PATH.read_bytes()
    except OSError as exc:
        raise FoundationBuildError(
            "FOUNDATION_INTERFACE_MISSING"
        ) from exc
    if actual_raw != expected_raw:
        raise FoundationBuildError(
            "FOUNDATION_INTERFACE_NOT_BYTE_EQUIVALENT"
        )
    interface = _strict_json(INTERFACE_PATH)
    validate_interface(interface)
    print(
        "RELEASE_FOUNDATION_BYTE_EQUIVALENT "
        f"schemas={len(interface['foundation_schemas'])} "
        f"conflicts={len(interface['policy_conflicts'])} "
        f"next_phase={interface['next_phase']} "
        f"artifact_digest={interface['artifact_digest']}"
    )


def main(argv: Sequence[str] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--print", dest="print_interface", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        _check()
    else:
        sys.stdout.buffer.write(render_interface())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FoundationBuildError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
