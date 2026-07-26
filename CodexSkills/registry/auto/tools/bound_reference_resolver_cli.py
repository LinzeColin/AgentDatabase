#!/usr/bin/env python3
"""Fail-closed production entrypoint for exact SkillVersion binding."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


AUTO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTO_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonicalize_object,
    parse_json_bytes,
)
from CodexSkills.registry.auto.runtime.binding_resolver import (  # noqa: E402
    RegistrySnapshotTrustTuple,
)
from CodexSkills.registry.auto.runtime.bootstrap import (  # noqa: E402
    ControlTrustTuple,
    bootstrap_runtime,
    require_bound_reference_resolver_authority,
)
from CodexSkills.registry.auto.runtime.core import (  # noqa: E402
    AutoRuntimeError,
)
from CodexSkills.registry.auto.tools.validate_auto import (  # noqa: E402
    TrustTuple,
)


MAX_REQUEST_BYTES = 256 * 1024


def _request() -> object:
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    if not raw or len(raw) > MAX_REQUEST_BYTES:
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_REQUEST_SIZE_INVALID"
        )
    try:
        value = parse_json_bytes(raw)
    except Exception as exc:
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_REQUEST_JSON_INVALID"
        ) from exc
    if not isinstance(value, dict):
        raise AutoRuntimeError(
            "BOUND_REFERENCE_RESOLVER_REQUEST_ROOT_INVALID"
        )
    return value


def main(argv: Sequence[str] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--verified-candidate-git-object-id", required=True)
    parser.add_argument("--expected-bundle-digest", required=True)
    parser.add_argument("--canonical-manifest-path", required=True)
    parser.add_argument(
        "--candidate-mode",
        choices=("CANDIDATE", "ACTIVE"),
        required=True,
    )
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
    args = parser.parse_args(argv)
    context = bootstrap_runtime(
        args.repo_root,
        TrustTuple(
            args.verified_candidate_git_object_id,
            args.expected_bundle_digest,
            args.canonical_manifest_path,
            args.candidate_mode,
        ),
        ControlTrustTuple(
            args.verified_control_git_object_id,
            args.expected_control_interface_raw_sha256,
            args.canonical_control_interface_path,
            args.control_mode,
        ),
        RegistrySnapshotTrustTuple(
            args.verified_registry_git_object_id,
            args.expected_registry_snapshot_digest,
            args.canonical_registry_snapshot_path,
            args.canonical_registry_snapshot_schema_id,
            args.registry_mode,
        ),
    )
    resolver = require_bound_reference_resolver_authority(context)
    sys.stdout.buffer.write(
        canonicalize_object(resolver.resolve(_request())) + b"\n"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AutoRuntimeError as exc:
        print(exc.code, file=sys.stderr)
        raise SystemExit(2)
