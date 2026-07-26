from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Dict, List

from .io import copy_clean, deterministic_zip, generate_manifest, safe_extract_zip, sha256_file
from .process import run_bounded
from .validation import detect_profile, validate_skill


def _run_optimizer_command(root: Path, arguments: List[str], expected_genesis_hash: str) -> Dict[str, Any]:
    command = [sys.executable, str(root / "scripts/wbi.py")] + arguments
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "WBI_NESTED_SELF_TEST": "1"}
    if expected_genesis_hash:
        env["WBI_EXPECTED_GENESIS_SHA256"] = expected_genesis_hash
    legacy = os.environ.get("WBI_COMMAND_TIMEOUT_SECONDS")
    if legacy:
        timeout = int(legacy)
    elif arguments and arguments[0] == "self-test":
        timeout = int(os.environ.get("WBI_SELF_TEST_TIMEOUT_SECONDS", "600"))
    else:
        timeout = int(os.environ.get("WBI_FAST_CHECK_TIMEOUT_SECONDS", "90"))
    if timeout <= 0:
        raise ValueError("optimizer command timeout must be positive")
    completed = run_bounded(command, cwd=root, env=env, timeout_seconds=timeout)
    stdout, stderr = completed["stdout"], completed["stderr"]
    return {
        "command": arguments,
        "returncode": completed["returncode"],
        "timed_out": completed["timed_out"],
        "timeout_seconds": completed["timeout_seconds"],
        "elapsed_seconds": completed["elapsed_seconds"],
        "stdout_sha256": __import__("hashlib").sha256(stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": __import__("hashlib").sha256(stderr.encode("utf-8")).hexdigest(),
        "stdout_tail": stdout[-2000:],
        "stderr_tail": stderr[-2000:],
    }


def package_skill(source: Path, output: Path, expected_genesis_hash: str = "", profile: str = "auto", verification_level: str = "structural") -> Dict[str, Any]:
    source = source.resolve()
    output = output.resolve()
    if verification_level not in {"structural", "release", "deep"}:
        return {"status": "FAIL", "stage": "verification-level", "errors": ["verification level must be structural, release or deep"]}
    resolved_profile = detect_profile(source, profile)
    if resolved_profile == "optimizer" and not expected_genesis_hash:
        return {"status": "FAIL", "stage": "external-genesis-anchor", "errors": ["optimizer packaging requires an external Genesis hash anchor"]}
    with tempfile.TemporaryDirectory(prefix="wbi-package-") as temp:
        staging_parent = Path(temp)
        staging = staging_parent / source.name
        try:
            copy_clean(source, staging)
        except Exception as exc:
            return {"status": "FAIL", "stage": "clean-copy", "errors": [str(exc)]}
        generate_manifest(staging)
        validation = validate_skill(
            staging, strict=True, expected_genesis_hash=expected_genesis_hash if resolved_profile == "optimizer" else "",
            profile=resolved_profile,
        )
        if validation["status"] != "PASS":
            return {"status": "FAIL", "stage": "prepackage-validation", "validation": validation}

        checks: Dict[str, Any] = {"profile": resolved_profile, "verification_level": verification_level, "prepackage_validation": validation["status"], "executed_target_code": False}
        if resolved_profile == "optimizer" and verification_level in {"release", "deep"}:
            try:
                verify = _run_optimizer_command(staging, ["verify-self", "--strict", "--expected-genesis-hash", expected_genesis_hash], expected_genesis_hash)
            except ValueError as exc:
                return {"status": "FAIL", "stage": "prepackage-command-policy", "errors": [str(exc)], "checks": checks}
            checks["prepackage_verify_self"] = verify
            if verify["returncode"] != 0:
                return {"status": "FAIL", "stage": "prepackage-verify-self", "checks": checks}
            try:
                smoke = _run_optimizer_command(staging, ["release-smoke", "--expected-genesis-hash", expected_genesis_hash], expected_genesis_hash)
            except ValueError as exc:
                return {"status": "FAIL", "stage": "prepackage-command-policy", "errors": [str(exc)], "checks": checks}
            checks["prepackage_release_smoke"] = smoke
            if smoke["returncode"] != 0:
                return {"status": "FAIL", "stage": "prepackage-release-smoke", "checks": checks}
        elif resolved_profile == "optimizer":
            checks["prepackage_verify_self"] = {"status": "SKIPPED_STRUCTURAL_LEVEL"}

        result = deterministic_zip(staging, output)
        extract_dir = staging_parent / "extract"
        try:
            safe_extract_zip(output, extract_dir)
        except Exception as exc:
            output.unlink(missing_ok=True)
            return {"status": "FAIL", "stage": "postextract-safety", "errors": [str(exc)]}
        extracted = extract_dir / source.name
        post = validate_skill(
            extracted, strict=True, expected_genesis_hash=expected_genesis_hash if resolved_profile == "optimizer" else "",
            profile=resolved_profile,
        )
        if post["status"] != "PASS":
            output.unlink(missing_ok=True)
            return {"status": "FAIL", "stage": "postextract-validation", "validation": post}
        checks["postextract_validation"] = post["status"]

        # Do not execute arbitrary target code. Teleiosis may run its own bundled
        # regression suite because it is the trusted optimizer being packaged.
        if resolved_profile == "optimizer" and verification_level in {"release", "deep"}:
            try:
                smoke = _run_optimizer_command(extracted, ["release-smoke", "--expected-genesis-hash", expected_genesis_hash], expected_genesis_hash)
            except ValueError as exc:
                output.unlink(missing_ok=True)
                return {"status": "FAIL", "stage": "postextract-command-policy", "errors": [str(exc)], "checks": checks}
            checks["postextract_release_smoke"] = smoke
            checks["executed_target_code"] = True
            if smoke["returncode"] != 0:
                output.unlink(missing_ok=True)
                return {"status": "FAIL", "stage": "postextract-release-smoke", "checks": checks}
            if not os.environ.get("WBI_NESTED_SELF_TEST"):
                try:
                    self_test = _run_optimizer_command(extracted, ["self-test"], expected_genesis_hash)
                except ValueError as exc:
                    output.unlink(missing_ok=True)
                    return {"status": "FAIL", "stage": "postextract-command-policy", "errors": [str(exc)], "checks": checks}
                checks["postextract_self_test"] = self_test
                if self_test["returncode"] != 0:
                    output.unlink(missing_ok=True)
                    return {"status": "FAIL", "stage": "postextract-self-test", "checks": checks}
            else:
                checks["postextract_self_test"] = {"status": "SKIPPED_NESTED_RECURSION_GUARD"}
        elif resolved_profile == "optimizer":
            checks["postextract_release_smoke"] = {"status": "SKIPPED_STRUCTURAL_LEVEL"}
            checks["postextract_self_test"] = {"status": "SKIPPED_STRUCTURAL_LEVEL"}

        result.update({
            "profile": resolved_profile,
            "checks": checks,
            "archive_sha256": sha256_file(output),
        })
        return result
