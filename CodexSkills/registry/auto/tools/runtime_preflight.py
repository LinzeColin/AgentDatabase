#!/usr/bin/env python3
"""Read-only Auto runtime preflight; callers must invoke an explicit Python."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

AUTO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTO_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from validate_auto import TrustTuple

from CodexSkills.registry.auto.runtime.bootstrap import (
    ControlTrustTuple,
    bootstrap_runtime,
)
from CodexSkills.registry.auto.runtime.binding_resolver import (
    RegistrySnapshotTrustTuple,
)
from CodexSkills.registry.auto.runtime.core import AutoRuntimeError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--verified-git-object-id", required=True)
    parser.add_argument("--expected-bundle-digest", required=True)
    parser.add_argument("--canonical-manifest-path", required=True)
    parser.add_argument("--mode", choices=("CANDIDATE", "ACTIVE"), required=True)
    parser.add_argument("--verified-control-git-object-id", required=True)
    parser.add_argument(
        "--expected-control-interface-raw-sha256",
        required=True,
    )
    parser.add_argument(
        "--canonical-control-interface-path",
        required=True,
    )
    parser.add_argument(
        "--control-mode",
        choices=("DRAFT_NON_ACTIVE_CONTROL",),
        required=True,
    )
    parser.add_argument(
        "--verified-registry-git-object-id",
        required=True,
    )
    parser.add_argument(
        "--expected-registry-snapshot-digest",
        required=True,
    )
    parser.add_argument(
        "--canonical-registry-snapshot-path",
        required=True,
    )
    parser.add_argument(
        "--canonical-registry-snapshot-schema-id",
        required=True,
    )
    parser.add_argument(
        "--registry-mode",
        choices=("REGISTERED",),
        required=True,
    )
    args = parser.parse_args()
    trust = TrustTuple(
        args.verified_git_object_id,
        args.expected_bundle_digest,
        args.canonical_manifest_path,
        args.mode,
    )
    control_trust = ControlTrustTuple(
        args.verified_control_git_object_id,
        args.expected_control_interface_raw_sha256,
        args.canonical_control_interface_path,
        args.control_mode,
    )
    snapshot_trust = RegistrySnapshotTrustTuple(
        args.verified_registry_git_object_id,
        args.expected_registry_snapshot_digest,
        args.canonical_registry_snapshot_path,
        args.canonical_registry_snapshot_schema_id,
        args.registry_mode,
    )
    context = bootstrap_runtime(
        args.repo_root,
        trust,
        control_trust,
        snapshot_trust,
    )
    versions = context.capabilities
    transition = context.control_interface["transition_contract"]
    resolver = context.binding_resolver
    resolver_status = (
        "VERIFIED_UNKNOWN_ONLY"
        if resolver is not None
        and resolver.all_current_versions_unknown_verified
        and resolver.binding_eligible_version_count == 0
        else "UNVERIFIED"
    )
    if (
        transition.get("auto_runtime_integration_complete") is not True
        or transition.get("runtime_state_write_permitted") is not True
    ):
        state_write = "CONTROL_SYNC_PENDING"
    elif (
        transition.get("repository_binding_integration_complete")
        is not True
    ):
        state_write = "REPOSITORY_CONTROL_SYNC_PENDING"
    elif transition.get("repository_bound") is not True:
        state_write = "REPOSITORY_AUTHORITY_PENDING"
    elif (
        transition.get("bound_reference_resolver_gate_satisfied")
        is not True
    ):
        state_write = "BOUND_REFERENCE_RESOLVER_PENDING"
    elif (
        transition.get("effective_runtime_state_write_permitted")
        is not True
    ):
        state_write = "EFFECTIVE_STATE_WRITE_AUTHORITY_PENDING"
    else:
        state_write = "ENABLED_BY_CONTROL"
    print(
        "AUTO_RUNTIME_PREFLIGHT_OK "
        f"mode={args.mode} schemas={len(context.contract.shared.schemas)} "
        f"policies={len(context.contract.shared.policies)} "
        f"state_write={state_write} "
        f"resolver={resolver_status} "
        f"python={versions['python']} jsonschema={versions['jsonschema']} "
        f"referencing={versions['referencing']} pyyaml={versions['pyyaml']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AutoRuntimeError as exc:
        print(exc.code)
        raise SystemExit(2)
