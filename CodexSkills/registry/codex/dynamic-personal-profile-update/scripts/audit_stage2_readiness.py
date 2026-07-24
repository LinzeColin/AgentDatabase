#!/usr/bin/env python3
"""Evaluate Stage 2 source, privacy, and capacity readiness from metadata only."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PHASE_ID = "STAGE2_PHASE2A_GOVERNED_DATA_READINESS"
CONTRACT_SCHEMA = "dynamic_profile.stage2_readiness_contract.v1"
EVIDENCE_SCHEMA = "dynamic_profile.stage2_github_evidence.v1"
REPORT_SCHEMA = "dynamic_profile.stage2_readiness_report.v1"
DEFAULT_CONTRACT = (
    Path(__file__).resolve().parents[1]
    / "references"
    / "stage2-readiness-contract.json"
)
MAX_JSON_BYTES = 1024 * 1024
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class ReadinessError(ValueError):
    """A public-safe readiness validation error."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReadinessError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink():
        raise ReadinessError(f"{label} must not be a symlink")
    if not path.is_file():
        raise ReadinessError(f"{label} is not a regular file")
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ReadinessError(f"{label} exceeds {MAX_JSON_BYTES} bytes")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ReadinessError(f"{label} is not readable UTF-8") from exc
    try:
        value = json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, ReadinessError) as exc:
        raise ReadinessError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ReadinessError(f"{label} root must be an object")
    return value


def expect(
    condition: bool,
    errors: list[str],
    code: str,
) -> None:
    if not condition:
        errors.append(code)


def validate_contract(contract: dict[str, Any]) -> None:
    errors: list[str] = []
    expect(contract.get("schema_version") == CONTRACT_SCHEMA, errors, "CONTRACT_SCHEMA")
    expect(contract.get("phase_id") == PHASE_ID, errors, "CONTRACT_PHASE")
    expect(contract.get("version") == "0.0.0.2", errors, "CONTRACT_VERSION")
    expect(contract.get("status") == "frozen", errors, "CONTRACT_STATUS")

    runtime = contract.get("runtime_boundary")
    expect(isinstance(runtime, dict), errors, "RUNTIME_BOUNDARY_TYPE")
    if isinstance(runtime, dict):
        expect(runtime.get("input_mode") == "derived_only", errors, "RUNTIME_INPUT_MODE")
        expect(runtime.get("raw_content_enabled") is False, errors, "RUNTIME_RAW_DISABLED")
        expect(
            runtime.get("network_enabled_in_profile_runtime") is False,
            errors,
            "RUNTIME_NETWORK_DISABLED",
        )
        expect(runtime.get("stable_memory_write") is False, errors, "STABLE_WRITE_DISABLED")
        expect(
            runtime.get("persistent_profile_outputs")
            == ["OpenAIDatabase/data/derived/profile/DYNAMIC_PROFILE.md"],
            errors,
            "PERSISTENT_OUTPUT_BOUNDARY",
        )

    source = contract.get("source_contract")
    expect(isinstance(source, dict), errors, "SOURCE_CONTRACT_TYPE")
    selected: list[dict[str, Any]] = []
    if isinstance(source, dict):
        repository = source.get("repository")
        expect(isinstance(repository, dict), errors, "SOURCE_REPOSITORY_TYPE")
        if isinstance(repository, dict):
            expect(
                repository.get("full_name") == "LinzeColin/Private-Database",
                errors,
                "SOURCE_REPOSITORY",
            )
            expect(repository.get("visibility") == "PRIVATE", errors, "SOURCE_VISIBILITY")
            expect(repository.get("archived") is False, errors, "SOURCE_ARCHIVED")
            expect(
                repository.get("transport") == "github_release_asset",
                errors,
                "SOURCE_TRANSPORT",
            )
        expect(source.get("instruction_trust") == "none", errors, "SOURCE_INSTRUCTION_TRUST")
        value = source.get("selected_assets")
        expect(isinstance(value, list), errors, "SELECTED_ASSETS_TYPE")
        if isinstance(value, list):
            selected = [item for item in value if isinstance(item, dict)]
            expect(len(selected) == len(value), errors, "SELECTED_ASSET_ENTRY_TYPE")
        expect(source.get("selected_asset_count") == 4, errors, "SELECTED_ASSET_COUNT")
        expect(len(selected) == 4, errors, "SELECTED_ASSET_LENGTH")

        source_ids: set[str] = set()
        asset_ids: set[int] = set()
        release_names: set[tuple[str, str]] = set()
        total = 0
        for index, asset in enumerate(selected):
            source_id = asset.get("source_id")
            asset_id = asset.get("asset_id")
            release_tag = asset.get("release_tag")
            asset_name = asset.get("asset_name")
            size = asset.get("size_bytes")
            digest = asset.get("sha256")
            expect(
                isinstance(source_id, str) and bool(source_id),
                errors,
                f"ASSET_{index}_SOURCE_ID",
            )
            expect(
                isinstance(asset.get("source_kind"), str)
                and bool(asset.get("source_kind")),
                errors,
                f"ASSET_{index}_SOURCE_KIND",
            )
            expect(
                isinstance(asset_id, int) and not isinstance(asset_id, bool) and asset_id > 0,
                errors,
                f"ASSET_{index}_ID",
            )
            expect(
                isinstance(release_tag, str) and bool(release_tag),
                errors,
                f"ASSET_{index}_RELEASE",
            )
            expect(
                isinstance(asset_name, str) and bool(asset_name),
                errors,
                f"ASSET_{index}_NAME",
            )
            expect(
                isinstance(size, int) and not isinstance(size, bool) and size > 0,
                errors,
                f"ASSET_{index}_SIZE",
            )
            expect(
                isinstance(digest, str) and bool(SHA256_RE.fullmatch(digest)),
                errors,
                f"ASSET_{index}_SHA256",
            )
            if isinstance(source_id, str):
                expect(source_id not in source_ids, errors, "DUPLICATE_SOURCE_ID")
                source_ids.add(source_id)
            if isinstance(asset_id, int):
                expect(asset_id not in asset_ids, errors, "DUPLICATE_ASSET_ID")
                asset_ids.add(asset_id)
            if isinstance(release_tag, str) and isinstance(asset_name, str):
                pair = (release_tag, asset_name)
                expect(pair not in release_names, errors, "DUPLICATE_RELEASE_ASSET")
                release_names.add(pair)
            if isinstance(size, int) and not isinstance(size, bool):
                total += size

        expect(
            source.get("selected_source_bytes") == total == 3276149855,
            errors,
            "SELECTED_SOURCE_BYTES",
        )
        exclusions = source.get("excluded_assets")
        expect(isinstance(exclusions, list) and len(exclusions) >= 1, errors, "EXCLUSIONS")
        if isinstance(exclusions, list):
            excluded_names = {
                item.get("asset_name")
                for item in exclusions
                if isinstance(item, dict)
            }
            expect(
                "codexproject_remote_non_main_branches_20260708.bundle"
                in excluded_names,
                errors,
                "GIT_BUNDLE_EXCLUSION",
            )
            expect(
                "codexproject_remote_non_main_branches_20260708.bundle"
                not in {item.get("asset_name") for item in selected},
                errors,
                "GIT_BUNDLE_SELECTED",
            )

    privacy = contract.get("privacy_contract")
    expect(isinstance(privacy, dict), errors, "PRIVACY_CONTRACT_TYPE")
    if isinstance(privacy, dict):
        required_privacy = {
            "phase2a_access": "metadata_only",
            "phase2a_raw_download": False,
            "phase2a_archive_open": False,
            "future_runner": "owner_controlled_local_private",
            "future_temp_outside_repository": True,
            "future_temp_mode": "0700",
            "one_asset_at_a_time": True,
            "raw_bytes_in_git": False,
            "raw_bytes_in_logs": False,
            "raw_bytes_in_artifacts": False,
            "raw_bytes_in_profile": False,
            "repository_public_raw_audit_required": True,
            "repository_high_risk_scan_required": True,
            "repository_privacy_findings_must_be_zero": True,
            "automatic_source_deletion": False,
            "embedded_instruction_trust": "none",
            "credential_values_may_be_echoed": False,
            "raw_baseline_requires_fresh_readiness_pass": True,
        }
        for key, expected in required_privacy.items():
            expect(privacy.get(key) == expected, errors, f"PRIVACY_{key.upper()}")

    capacity = contract.get("capacity_contract")
    expect(isinstance(capacity, dict), errors, "CAPACITY_CONTRACT_TYPE")
    if isinstance(capacity, dict) and isinstance(source, dict):
        source_bytes = source.get("selected_source_bytes")
        multiplier = capacity.get("scratch_multiplier")
        headroom = capacity.get("scratch_headroom_bytes")
        required = capacity.get("required_scratch_bytes")
        expect(multiplier == 2, errors, "CAPACITY_MULTIPLIER")
        expect(headroom == 2147483648, errors, "CAPACITY_HEADROOM")
        if all(isinstance(value, int) for value in (source_bytes, multiplier, headroom)):
            expect(
                required == source_bytes * multiplier + headroom == 8699783358,
                errors,
                "CAPACITY_REQUIRED_BYTES",
            )
        expect(
            capacity.get("processing_mode") == "one_asset_at_a_time_streaming",
            errors,
            "CAPACITY_PROCESSING_MODE",
        )
        expect(
            capacity.get("full_archive_expansion_persisted") is False,
            errors,
            "CAPACITY_NO_FULL_EXPANSION",
        )
        expect(
            capacity.get("recheck_before_raw_baseline") is True,
            errors,
            "CAPACITY_RECHECK",
        )

    if errors:
        raise ReadinessError("contract validation failed: " + ",".join(sorted(set(errors))))


def source_gate(
    contract: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[str, list[str]]:
    errors: list[str] = []
    expect(evidence.get("schema_version") == EVIDENCE_SCHEMA, errors, "EVIDENCE_SCHEMA")
    observed_at = evidence.get("observed_at")
    expect(
        isinstance(observed_at, str) and bool(UTC_RE.fullmatch(observed_at)),
        errors,
        "EVIDENCE_OBSERVED_AT",
    )
    if isinstance(observed_at, str) and UTC_RE.fullmatch(observed_at):
        try:
            datetime.strptime(observed_at, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            errors.append("EVIDENCE_OBSERVED_AT")

    expected_repo = contract["source_contract"]["repository"]
    repository = evidence.get("repository")
    expect(isinstance(repository, dict), errors, "EVIDENCE_REPOSITORY_TYPE")
    if isinstance(repository, dict):
        expect(
            repository.get("full_name") == expected_repo["full_name"],
            errors,
            "REMOTE_REPOSITORY_MISMATCH",
        )
        expect(repository.get("visibility") == "PRIVATE", errors, "REMOTE_NOT_PRIVATE")
        expect(repository.get("private") is True, errors, "REMOTE_PRIVATE_FLAG")
        expect(repository.get("archived") is False, errors, "REMOTE_ARCHIVED")

    releases_value = evidence.get("releases")
    expect(isinstance(releases_value, list), errors, "EVIDENCE_RELEASES_TYPE")
    releases: dict[str, dict[str, Any]] = {}
    if isinstance(releases_value, list):
        for release in releases_value:
            if not isinstance(release, dict) or not isinstance(release.get("tag_name"), str):
                errors.append("EVIDENCE_RELEASE_ENTRY")
                continue
            tag = release["tag_name"]
            if tag in releases:
                errors.append("EVIDENCE_DUPLICATE_RELEASE")
                continue
            releases[tag] = release

    for expected in contract["source_contract"]["selected_assets"]:
        tag = expected["release_tag"]
        release = releases.get(tag)
        if release is None:
            errors.append(f"MISSING_RELEASE:{tag}")
            continue
        if release.get("draft") is not False:
            errors.append(f"RELEASE_DRAFT:{tag}")
        if release.get("prerelease") is not False:
            errors.append(f"RELEASE_PRERELEASE:{tag}")
        assets_value = release.get("assets")
        if not isinstance(assets_value, list):
            errors.append(f"RELEASE_ASSETS_TYPE:{tag}")
            continue
        by_id: dict[int, dict[str, Any]] = {}
        for asset in assets_value:
            if not isinstance(asset, dict):
                errors.append(f"RELEASE_ASSET_ENTRY:{tag}")
                continue
            asset_id = asset.get("id")
            if (
                not isinstance(asset_id, int)
                or isinstance(asset_id, bool)
                or asset_id <= 0
            ):
                errors.append(f"RELEASE_ASSET_ID:{tag}")
                continue
            if asset_id in by_id:
                errors.append(f"DUPLICATE_ASSET_ID:{tag}:{asset_id}")
                continue
            by_id[asset_id] = asset
        actual = by_id.get(expected["asset_id"])
        if actual is None:
            errors.append(f"MISSING_ASSET:{expected['source_id']}")
            continue
        comparisons = {
            "name": expected["asset_name"],
            "size": expected["size_bytes"],
            "state": "uploaded",
            "digest": "sha256:" + expected["sha256"],
        }
        for field, expected_value in comparisons.items():
            if actual.get(field) != expected_value:
                errors.append(
                    f"ASSET_{field.upper()}_MISMATCH:{expected['source_id']}"
                )

    return ("PASS" if not errors else "FAIL", sorted(set(errors)))


def privacy_gate(
    contract: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[str, list[str]]:
    privacy = contract["privacy_contract"]
    errors: list[str] = []
    contract_safe = (
        privacy["phase2a_access"] == "metadata_only"
        and privacy["phase2a_raw_download"] is False
        and privacy["phase2a_archive_open"] is False
        and privacy["raw_bytes_in_git"] is False
        and privacy["raw_bytes_in_logs"] is False
        and privacy["raw_bytes_in_artifacts"] is False
        and privacy["raw_bytes_in_profile"] is False
        and privacy["embedded_instruction_trust"] == "none"
        and privacy["credential_values_may_be_echoed"] is False
    )
    if not contract_safe:
        errors.append("PRIVACY_INVARIANT")

    repository_privacy = evidence.get("repository_privacy")
    if not isinstance(repository_privacy, dict):
        errors.append("REPOSITORY_PRIVACY_EVIDENCE_MISSING")
        return "FAIL", errors

    public_raw = repository_privacy.get("public_raw_audit")
    if not isinstance(public_raw, dict):
        errors.append("PUBLIC_RAW_AUDIT_EVIDENCE_MISSING")
    else:
        if public_raw.get("status") != "PASS":
            errors.append("PUBLIC_RAW_AUDIT_NOT_PASS")
        finding_count = public_raw.get("credential_or_private_text_file_count")
        if (
            not isinstance(finding_count, int)
            or isinstance(finding_count, bool)
            or finding_count != 0
        ):
            errors.append("PUBLIC_RAW_PRIVATE_TEXT_FINDINGS")
        for field in (
            "unmarked_binary_file_count",
            "invalid_binary_marker_file_count",
            "invalid_json_file_count",
            "oversize_file_count",
        ):
            value = public_raw.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value != 0:
                errors.append(f"PUBLIC_RAW_{field.upper()}")

    high_risk = repository_privacy.get("high_risk_scan")
    if not isinstance(high_risk, dict):
        errors.append("HIGH_RISK_SCAN_EVIDENCE_MISSING")
    else:
        if high_risk.get("status") != "PASS":
            errors.append("HIGH_RISK_SCAN_NOT_PASS")
        finding_count = high_risk.get("high_risk_secret_hit_count")
        if (
            not isinstance(finding_count, int)
            or isinstance(finding_count, bool)
            or finding_count != 0
        ):
            errors.append("HIGH_RISK_SECRET_FINDINGS")
        tracked_count = high_risk.get("tracked_raw_private_file_count")
        if (
            not isinstance(tracked_count, int)
            or isinstance(tracked_count, bool)
            or tracked_count != 0
        ):
            errors.append("TRACKED_RAW_PRIVATE_FINDINGS")

    return ("PASS" if not errors else "FAIL", sorted(set(errors)))


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def capacity_gate(
    contract: dict[str, Any],
    repo_root: Path,
    scratch_root: Path,
) -> tuple[str, list[str], int, int]:
    errors: list[str] = []
    if not repo_root.exists() or not (repo_root / ".git").exists():
        errors.append("REPO_ROOT_INVALID")
    if not scratch_root.is_dir():
        errors.append("SCRATCH_ROOT_INVALID")
    resolved_repo = repo_root.resolve(strict=False)
    resolved_scratch = scratch_root.resolve(strict=False)
    if is_within(resolved_scratch, resolved_repo):
        errors.append("SCRATCH_ROOT_INSIDE_REPOSITORY")

    required = contract["capacity_contract"]["required_scratch_bytes"]
    available = 0
    if not errors:
        try:
            available = shutil.disk_usage(resolved_scratch).free
        except OSError:
            errors.append("SCRATCH_CAPACITY_UNREADABLE")
    if available < required:
        errors.append("SCRATCH_CAPACITY_INSUFFICIENT")
    return ("PASS" if not errors else "FAIL", sorted(set(errors)), required, available)


def build_report(
    contract: dict[str, Any],
    evidence: dict[str, Any],
    repo_root: Path,
    scratch_root: Path,
) -> dict[str, Any]:
    source_status, source_errors = source_gate(contract, evidence)
    privacy_status, privacy_errors = privacy_gate(contract, evidence)
    capacity_status, capacity_errors, required, available = capacity_gate(
        contract,
        repo_root,
        scratch_root,
    )
    ready = all(
        status == "PASS"
        for status in (source_status, privacy_status, capacity_status)
    )
    return {
        "schema_version": REPORT_SCHEMA,
        "phase_id": PHASE_ID,
        "contract_version": contract["version"],
        "status": "READY" if ready else "NOT_READY",
        "gates": {
            "source": {"status": source_status, "errors": source_errors},
            "privacy": {"status": privacy_status, "errors": privacy_errors},
            "capacity": {
                "status": capacity_status,
                "errors": capacity_errors,
                "required_scratch_bytes": required,
                "available_scratch_bytes": available,
            },
        },
        "selected_asset_count": contract["source_contract"]["selected_asset_count"],
        "selected_source_bytes": contract["source_contract"]["selected_source_bytes"],
        "raw_content_read": False,
        "network_used": False,
        "persistent_output_written": False,
        "raw_baseline_authorized_by_evidence": ready,
        "evidence_observed_at": evidence.get("observed_at"),
    }


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Stage 2 readiness from independently fetched metadata."
    )
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        contract = load_json(args.contract, "contract")
        validate_contract(contract)
        evidence = load_json(args.evidence, "evidence")
        report = build_report(
            contract,
            evidence,
            args.repo_root,
            args.scratch_root,
        )
    except (ReadinessError, OSError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": REPORT_SCHEMA,
                    "phase_id": PHASE_ID,
                    "status": "ERROR",
                    "error": str(exc),
                    "raw_content_read": False,
                    "network_used": False,
                    "persistent_output_written": False,
                    "raw_baseline_authorized_by_evidence": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
