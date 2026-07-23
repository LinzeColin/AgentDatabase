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
    context = bootstrap_runtime(args.repo_root, trust, control_trust)
    versions = context.capabilities
    state_write = (
        "ENABLED_BY_CONTROL"
        if context.control_interface["transition_contract"][
            "auto_runtime_integration_complete"
        ]
        else "CONTROL_SYNC_PENDING"
    )
    print(
        "AUTO_RUNTIME_PREFLIGHT_OK "
        f"mode={args.mode} schemas={len(context.contract.shared.schemas)} "
        f"policies={len(context.contract.shared.policies)} "
        f"state_write={state_write} "
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
