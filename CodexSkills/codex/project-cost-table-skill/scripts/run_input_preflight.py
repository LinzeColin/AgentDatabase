#!/usr/bin/env python3
"""Run only the metadata-first input gate and publish its absolute output locator."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import replace
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.input_gate import (  # noqa: E402
    InputGateError,
    InputRequirements,
    MetricCatalog,
    OperationRequest,
    evaluate_input_sufficiency,
    output_locator,
    publish_input_gate_outputs,
    render_missing_input_prompt,
    resolve_operation_output_dir,
    verify_detached_seal,
)
from project_cost_table.inventory import InventoryError, scan_inventory_metadata  # noqa: E402
from project_cost_table.manifest import ManifestError, load_input_manifest  # noqa: E402
from project_cost_table.private_runtime import ensure_private_runtime  # noqa: E402
from project_cost_table.resolutions import ResolutionError, load_input_resolution  # noqa: E402
from project_cost_table.security import SecurityProfile, SecurityProfileError  # noqa: E402


INCOMPLETE_PRIOR_STATUSES = frozenset(
    {"NEEDS_SUPPLEMENT", "NEEDS_EXPLICIT_HANDLING", "BLOCKED_NON_WAIVABLE"}
)


def _load_request(path: Path) -> OperationRequest:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise InputGateError("REQUEST_UNAVAILABLE", "private operation request cannot be accessed") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise InputGateError("REQUEST_PATH_UNSAFE", "private operation request must be a single-link regular file")
    if metadata.st_size > 1024 * 1024:
        raise InputGateError("REQUEST_TOO_LARGE", "private operation request exceeds its metadata ceiling")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputGateError("REQUEST_PARSE_ERROR", "private operation request is not valid UTF-8 JSON") from exc
    if not isinstance(raw, dict):
        raise InputGateError("REQUEST_NOT_MAPPING", "private operation request must be an object")
    return OperationRequest.from_mapping(raw)


def _load_prior_request_hash(path: Path, *, expected_run_id: str) -> str:
    """Load a sealed prior insufficiency report without reading any raw source body."""

    value = Path(path)
    try:
        metadata = value.lstat()
    except OSError as exc:
        raise InputGateError("PRIOR_REPORT_UNAVAILABLE", "prior sufficiency report cannot be accessed") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise InputGateError("PRIOR_REPORT_PATH_UNSAFE", "prior sufficiency report must be a single-link regular file")
    if metadata.st_size > 1024 * 1024:
        raise InputGateError("PRIOR_REPORT_TOO_LARGE", "prior sufficiency report exceeds its metadata ceiling")
    if value.name != "input_sufficiency_report.json" or not verify_detached_seal(value.parent):
        raise InputGateError("PRIOR_REPORT_SEAL_INVALID", "prior sufficiency report is not in a valid sealed run directory")
    try:
        payload = value.read_bytes()
        seal_lines = (value.parent / "run_seal.sha256").read_text(encoding="ascii").splitlines()
        raw = json.loads(payload.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputGateError("PRIOR_REPORT_PARSE_ERROR", "prior sufficiency report is not valid UTF-8 JSON") from exc
    expected_seal_line = "%s  input_sufficiency_report.json" % hashlib.sha256(payload).hexdigest()
    if expected_seal_line not in seal_lines:
        raise InputGateError("PRIOR_REPORT_SEAL_INVALID", "prior report is not covered by its detached seal")
    try:
        after = value.lstat()
    except OSError as exc:
        raise InputGateError("PRIOR_REPORT_CHANGED", "prior sufficiency report changed during verification") from exc
    identity_before = (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns, metadata.st_nlink)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_nlink)
    if identity_before != identity_after:
        raise InputGateError("PRIOR_REPORT_CHANGED", "prior sufficiency report changed during verification")
    if not isinstance(raw, dict) or raw.get("schema_version") != "kmfa.project_cost.input_sufficiency_report.v1":
        raise InputGateError("PRIOR_REPORT_SCHEMA_DRIFT", "prior sufficiency report schema version is unsupported")
    request_hash = raw.get("request_hash")
    if raw.get("run_id") != expected_run_id:
        raise InputGateError("PRIOR_REPORT_RUN_MISMATCH", "prior sufficiency report belongs to another run")
    if raw.get("overall_status") not in INCOMPLETE_PRIOR_STATUSES or raw.get("user_action_required") is not True:
        raise InputGateError("PRIOR_REPORT_NOT_INCOMPLETE", "input resolution must bind an incomplete prior report")
    if not isinstance(request_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", request_hash):
        raise InputGateError("PRIOR_REPORT_REQUEST_HASH_INVALID", "prior sufficiency report request hash is invalid")
    try:
        recorded_output = Path(raw["output_dir"]).resolve(strict=True)
        actual_output = value.parent.resolve(strict=True)
    except (KeyError, OSError, TypeError) as exc:
        raise InputGateError("PRIOR_REPORT_OUTPUT_INVALID", "prior sufficiency report output locator is invalid") from exc
    if recorded_output != actual_output:
        raise InputGateError("PRIOR_REPORT_OUTPUT_MISMATCH", "prior sufficiency report moved from its sealed output directory")
    return request_hash


def _is_valid_standalone_module_root(module_root: Path) -> bool:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    try:
        skills_root = (codex_home / "skills").resolve(strict=True)
    except OSError:
        return False
    if module_root.parent != skills_root or module_root.name != "project-cost-table-skill":
        return False
    required_files = (
        "SKILL.md",
        "VERSION",
        "config/input_requirements.yml",
        "config/metric_catalog.yml",
        "config/security_limits.yml",
        "src/project_cost_table/__init__.py",
        "scripts/run_input_preflight.py",
    )
    for relative in required_files:
        candidate = module_root / relative
        if candidate.is_symlink() or not candidate.is_file():
            return False
    return True


def _discover_repo_root(module_root: Path) -> Path:
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(module_root),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        if _is_valid_standalone_module_root(module_root):
            return module_root
        raise InputGateError(
            "STANDALONE_MODULE_ROOT_INVALID",
            "repository metadata is unavailable and the standalone Skill package is incomplete",
        ) from exc
    if not output:
        raise InputGateError("REPO_ROOT_INVALID", "repository root discovery returned an empty path")
    try:
        repo_root = Path(output).resolve(strict=True)
        module_root.relative_to(repo_root)
    except (OSError, ValueError) as exc:
        raise InputGateError("REPO_ROOT_INVALID", "module root is outside the discovered repository") from exc
    return repo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--module-root", type=Path, default=MODULE_ROOT)
    args = parser.parse_args()
    try:
        module_root = args.module_root.resolve(strict=True)
        repo_root = _discover_repo_root(module_root)
        request = _load_request(args.request)
        ensure_private_runtime(module_root)
        private_runtime = module_root / "private_runtime"
        output_error = None
        try:
            output_dir = resolve_operation_output_dir(
                request,
                private_runtime_root=private_runtime,
                repo_root=repo_root,
            )
        except InputGateError as exc:
            output_error = exc.code
            fallback_request = replace(request, output_dir=None)
            output_dir = resolve_operation_output_dir(
                fallback_request,
                private_runtime_root=private_runtime,
                repo_root=repo_root,
            )
        requirements = InputRequirements.from_yaml(module_root / "config" / "input_requirements.yml")
        metric_catalog = MetricCatalog.from_yaml(module_root / "config" / "metric_catalog.yml")
        try:
            security_profile = SecurityProfile.from_yaml(module_root / "config" / "security_limits.yml")
            security_capability_present = True
        except SecurityProfileError:
            security_profile = None
            security_capability_present = False
        manifest = None
        manifest_error = None
        if request.manifest_path:
            try:
                manifest = load_input_manifest(Path(request.manifest_path))
            except ManifestError as exc:
                manifest_error = exc.code
        inventory_entries = ()
        inventory_error = None
        if request.input_root:
            try:
                inventory_entries = scan_inventory_metadata(Path(request.input_root))
            except InventoryError as exc:
                inventory_error = exc.code
        if bool(request.resolution_path) != bool(request.prior_sufficiency_report_path):
            raise InputGateError(
                "REQUEST_RESOLUTION_BINDING_INCOMPLETE",
                "resolution and prior sufficiency report paths must be supplied together",
            )
        resolution = load_input_resolution(Path(request.resolution_path)) if request.resolution_path else None
        prior_request_hash = (
            _load_prior_request_hash(Path(request.prior_sufficiency_report_path), expected_run_id=request.run_id)
            if request.prior_sufficiency_report_path
            else None
        )
        report = evaluate_input_sufficiency(
            request,
            requirements=requirements,
            metric_catalog=metric_catalog,
            output_dir=output_dir,
            manifest=manifest,
            inventory_entries=inventory_entries,
            security_capability_present=security_capability_present,
            security_profile_id=security_profile.profile_id if security_profile else None,
            resolution=resolution,
            prior_request_hash=prior_request_hash,
            manifest_error_code=manifest_error,
            inventory_error_code=inventory_error,
            output_dir_error_code=output_error,
        )
        outputs = publish_input_gate_outputs(report, resolution=resolution)
        if not verify_detached_seal(outputs.output_dir):
            raise InputGateError("RUN_SEAL_VERIFICATION_FAILED", "input-gate detached seal did not verify")
        prompt = render_missing_input_prompt(report)
        if prompt:
            print(prompt.rstrip())
        result_status = "NEEDS_USER_INPUT" if report.user_action_required else "INPUT_SUFFICIENT"
        next_step = (
            "supplement or explicitly resolve the numbered missing inputs"
            if report.user_action_required
            else "continue to bound source security/schema/digest preflight"
        )
        print(output_locator(result_status=result_status, outputs=outputs, next_step=next_step))
        return 2 if report.user_action_required else 0
    except (InputGateError, InventoryError, ManifestError, ResolutionError, OSError) as exc:
        code = getattr(exc, "code", "INPUT_PREFLIGHT_ERROR")
        message = getattr(exc, "message", "input preflight failed safely")
        print(json.dumps({"status": "FAILED", "code": code, "message": message}, ensure_ascii=False))
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
