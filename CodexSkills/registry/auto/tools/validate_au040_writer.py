#!/usr/bin/env python3
"""Run the development-only unbound AU-040 writer closure check."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(
    0,
    str(REPO_ROOT / "CodexSkills" / "governance" / "tools"),
)

from CodexSkills.governance.tools.validate_mechanism import TrustTuple
from CodexSkills.registry.auto.runtime.bootstrap import (
    CONTROL_INTERFACE_PATH,
    CONTROL_MODE,
    ControlTrustTuple,
)
from CodexSkills.registry.auto.runtime.core import AutoRuntimeError
from CodexSkills.registry.auto.runtime.writer_shadow import (
    validate_unbound_writer_candidate,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--verified-git-object-id", required=True)
    parser.add_argument("--expected-bundle-digest", required=True)
    parser.add_argument(
        "--canonical-manifest-path",
        required=True,
    )
    parser.add_argument("--mode", required=True)
    parser.add_argument(
        "--verified-control-git-object-id",
        required=True,
    )
    parser.add_argument(
        "--expected-control-interface-raw-sha256",
        required=True,
    )
    parser.add_argument(
        "--canonical-control-interface-path",
        default=CONTROL_INTERFACE_PATH,
    )
    parser.add_argument("--control-mode", default=CONTROL_MODE)
    args = parser.parse_args()
    evidence = validate_unbound_writer_candidate(
        args.repo_root,
        TrustTuple(
            args.verified_git_object_id,
            args.expected_bundle_digest,
            args.canonical_manifest_path,
            args.mode,
        ),
        ControlTrustTuple(
            args.verified_control_git_object_id,
            args.expected_control_interface_raw_sha256,
            args.canonical_control_interface_path,
            args.control_mode,
        ),
    )
    print(
        "AUTO_AU040_WRITER_SHADOW "
        f"status={evidence.status} "
        f"schemas={evidence.schema_count} "
        f"policies={evidence.policy_count} "
        f"modules={evidence.current_module_count} "
        "state_write=FORBIDDEN"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AutoRuntimeError as exc:
        print(exc.code, file=sys.stderr)
        raise SystemExit(2)
