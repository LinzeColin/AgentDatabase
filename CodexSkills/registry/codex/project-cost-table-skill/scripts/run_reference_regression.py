#!/usr/bin/env python3
"""Run one private, hash-bound R10 reference replay without calculate imports."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_ROOT / "src"))

from project_cost_table import __version__
from project_cost_table.reference_replay import (
    ReferenceReplayError,
    ReferenceReplayRequest,
    run_reference_replay,
)
from project_cost_table.security import SecurityProfile
from project_cost_table.statuses import ReplayFidelityStatus


def _config_hash() -> str:
    digest = hashlib.sha256()
    for relative in (
        "config/security_limits.yml",
        "config/status_codes.yml",
        "schemas/reference_baseline.schema.json",
        "schemas/reference_baseline_import.schema.json",
        "schemas/reference_replay_result.schema.json",
        "schemas/run_manifest.schema.json",
        "schemas/output_index.schema.json",
    ):
        path = MODULE_ROOT / relative
        digest.update(relative.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(path.read_bytes())
        digest.update(b"\x00")
    return digest.hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hash-bound private reference replay. This command never calculates current facts."
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--baseline-manifest")
    parser.add_argument("--baseline-root")
    parser.add_argument("--baseline-relative-path")
    parser.add_argument("--baseline-sha256")
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--expected-project-count", type=int)
    parser.add_argument("--output-dir", required=True)
    return parser


def _baseline_binding(args: argparse.Namespace):
    if args.baseline_manifest:
        if any(
            value is not None
            for value in (
                args.baseline_root,
                args.baseline_relative_path,
                args.baseline_sha256,
                args.expected_project_count,
            )
        ):
            raise ReferenceReplayError(
                "REPLAY_BASELINE_ARGUMENT_CONFLICT",
                "baseline manifest cannot be mixed with direct baseline arguments",
            )
        path = Path(args.baseline_manifest).expanduser()
        try:
            metadata = path.lstat()
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ReferenceReplayError(
                "REPLAY_BASELINE_MANIFEST_UNREADABLE",
                "private baseline import manifest cannot be read",
            ) from exc
        if path.is_symlink() or not path.is_file() or metadata.st_nlink != 1:
            raise ReferenceReplayError(
                "REPLAY_BASELINE_MANIFEST_UNSAFE",
                "private baseline import manifest must be a single-link regular file",
            )
        expected_fields = {
            "schema_version",
            "classification",
            "baseline_file",
            "baseline_sha256",
            "expected_project_count",
            "task_pack_version",
            "source_package_manifest_sha256",
        }
        if (
            not isinstance(payload, dict)
            or set(payload) != expected_fields
            or payload.get("schema_version") != "kmfa.project_cost.reference_baseline_import.private.v1"
            or payload.get("classification") != "PRIVATE_RUNTIME"
        ):
            raise ReferenceReplayError(
                "REPLAY_BASELINE_MANIFEST_SCHEMA",
                "private baseline import manifest fields differ from v1",
            )
        return (
            path.parent,
            payload["baseline_file"],
            payload["baseline_sha256"],
            payload["expected_project_count"],
        )
    direct = (
        args.baseline_root,
        args.baseline_relative_path,
        args.baseline_sha256,
        args.expected_project_count,
    )
    if any(value is None for value in direct):
        raise ReferenceReplayError(
            "REPLAY_BASELINE_ARGUMENTS_MISSING",
            "provide one baseline manifest or all direct baseline arguments",
        )
    return Path(args.baseline_root).expanduser(), args.baseline_relative_path, args.baseline_sha256, args.expected_project_count


def main() -> int:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).expanduser().absolute()
    try:
        baseline_root, baseline_relative_path, baseline_sha256, expected_project_count = _baseline_binding(args)
    except ReferenceReplayError as exc:
        print(
            json.dumps(
                {
                    "status": "FAILED_BEFORE_ATOMIC_OUTPUT",
                    "error_code": exc.code,
                    "output_dir": str(output_dir),
                    "next_step": "修复 private baseline import manifest 后重试。",
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 3
    request = ReferenceReplayRequest(
        run_id=args.run_id,
        as_of=args.as_of,
        input_root=Path(args.input_root).expanduser(),
        baseline_root=baseline_root,
        baseline_relative_path=baseline_relative_path,
        baseline_sha256=baseline_sha256,
        output_dir=output_dir,
        expected_project_count=expected_project_count,
        security_profile=SecurityProfile.from_yaml(MODULE_ROOT / "config" / "security_limits.yml"),
        code_version=__version__,
        config_hash=_config_hash(),
    )
    try:
        result = run_reference_replay(request)
    except ReferenceReplayError as exc:
        print(
            json.dumps(
                {
                    "status": "FAILED_BEFORE_ATOMIC_OUTPUT",
                    "error_code": exc.code,
                    "output_dir": str(output_dir),
                    "next_step": "修复输入/路径门禁后使用新 run ID 和新输出目录重试。",
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 3
    print(
        json.dumps(
            {
                "status": (
                    "REFERENCE_REPLAY_EXACT"
                    if result.replay_fidelity_status == ReplayFidelityStatus.EXACT
                    else result.status_planes.generation_status.value
                ),
                "output_dir": str(result.output_dir),
                "primary_output": str(result.primary_output),
                "output_index": str(result.output_index_md),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    print(result.locator_text())
    return 0 if result.replay_fidelity_status == ReplayFidelityStatus.EXACT else 3


if __name__ == "__main__":
    raise SystemExit(main())
