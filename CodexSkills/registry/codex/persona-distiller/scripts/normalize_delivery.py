#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import stat
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from delivery_builder import build_full_delivery  # noqa: E402
from persona_registry import inspect_runtime_zip  # noqa: E402

REPORT_SUFFIXES = {
    ".csv",
    ".docx",
    ".json",
    ".jsonl",
    ".md",
    ".pdf",
    ".ps1",
    ".py",
    ".rst",
    ".sha256",
    ".sh",
    ".txt",
    ".yaml",
    ".yml",
}
FORBIDDEN_PARTS = {
    "raw",
    "holdout",
    "private-sources",
    "runtime-history",
    "__pycache__",
}


def runtime_members(runtime_zip: Path) -> tuple[str, dict[str, bytes]]:
    with zipfile.ZipFile(runtime_zip) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        top_levels = {PurePosixPath(name).parts[0] for name in names}
        if len(top_levels) != 1:
            raise ValueError("runtime ZIP must have exactly one top-level directory")
        top = next(iter(top_levels))
        return top, {
            PurePosixPath(name).relative_to(top).as_posix(): archive.read(name)
            for name in names
        }


def json_member(members: dict[str, bytes], relative: str) -> dict[str, Any] | None:
    payload = members.get(relative)
    if payload is None:
        return None
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def jsonl_member(members: dict[str, bytes], relative: str) -> list[dict[str, Any]]:
    payload = members.get(relative)
    if payload is None:
        return []
    result = []
    try:
        lines = payload.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return []
    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            result.append(value)
    return result


def legacy_audit(runtime_zip: Path) -> dict[str, dict[str, Any]]:
    _, members = runtime_members(runtime_zip)
    meta = json_member(members, "meta.json") or {}
    quality = (
        json_member(members, "audit/quality-release.json")
        or json_member(members, "reports/quality-release.json")
    )
    coverage = (
        json_member(members, "audit/coverage-map.json")
        or json_member(members, "research/coverage-map.json")
    )
    source_records = jsonl_member(members, "evidence/source-ledger.jsonl")
    rights_counts = collections.Counter(
        str(record.get("rights") or "unknown") for record in source_records
    )
    quality_metrics = dict(quality.get("metrics") or {}) if quality else {}
    evaluation_status = (
        "passed"
        if quality and quality.get("passed") is True
        else "not-available-in-source-artifact"
    )
    coverage_status = "passed" if coverage else "not-available-in-source-artifact"
    review_independence = meta.get("evaluation_independence")
    review_status = (
        "passed-with-serialized-isolation"
        if isinstance(review_independence, str) and review_independence
        else "not-available-in-source-artifact"
    )
    return {
        "verification.json": {
            "schema_version": "1.0",
            "status": "passed-runtime-integrity-only",
            "checks": {
                "runtime_structure": True,
                "runtime_checksums": True,
                "runtime_privacy_contract": True,
                "full_original_release_gate": bool(quality and quality.get("passed") is True),
            },
            "claims": (
                ["Original source artifact contains a passing release-quality record."]
                if quality and quality.get("passed") is True
                else [
                    "Runtime bytes and their internal checksums passed migration inspection.",
                    "A full original release-quality record was not available.",
                ]
            ),
        },
        "provenance.json": {
            "schema_version": "1.0",
            "status": (
                "passed-sanitized-runtime-ledger"
                if source_records
                else "not-available-in-source-artifact"
            ),
            "builder_version": meta.get("builder_version"),
            "subject_origin": meta.get("subject_origin"),
            "research_cutoff": meta.get("research_cutoff"),
            "source_record_count": len(source_records),
            "rights_summary": dict(sorted(rights_counts.items())),
            "private_paths_included": False,
            "source_bodies_included": False,
            "claims": [],
        },
        "source-coverage.json": {
            "schema_version": "1.0",
            "status": coverage_status,
            "research_cutoff": meta.get("research_cutoff"),
            "details": coverage or {},
            "lane_source_counts": quality_metrics.get("lane_source_counts", {}),
            "primary_ratio": quality_metrics.get("primary_ratio"),
            "remaining_gaps": (coverage or {}).get("remaining_gaps", []),
            "claims": [],
        },
        "evaluation-summary.json": {
            "schema_version": "1.0",
            "status": evaluation_status,
            "profile": (quality or {}).get("profile"),
            "suite_counts": quality_metrics.get("eval_suite_counts", {}),
            "candidate_overall": quality_metrics.get("candidate_overall"),
            "baseline_overall": quality_metrics.get("baseline_overall"),
            "candidate_baseline_delta": quality_metrics.get("candidate_baseline_delta"),
            "independence": review_independence or "not-available-in-source-artifact",
            "frozen_output_hashes": {},
            "claims": [],
        },
        "review-record.json": {
            "schema_version": "1.0",
            "status": review_status,
            "independence": review_independence or "not-available-in-source-artifact",
            "same_context_roleplay_claimed_as_independent": False,
            "claims": [],
        },
    }


def safe_member(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name or "\x00" in name:
        raise ValueError(f"unsafe source-delivery member: {name}")
    return path


def extract_source_reports(
    source_delivery: Path,
    destination: Path,
    runtime_sha256: str,
) -> list[tuple[Path, str]]:
    reports: list[tuple[Path, str]] = []

    def preserve(payload: bytes, report_relative: PurePosixPath) -> None:
        if any(part.casefold() in FORBIDDEN_PARTS for part in report_relative.parts):
            return
        if (
            report_relative.suffix.casefold() not in REPORT_SUFFIXES
            and report_relative.name not in {"VERSION", "LICENSE"}
        ):
            return
        output = destination / report_relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(payload)
        reports.append((output, report_relative.as_posix()))

    with zipfile.ZipFile(source_delivery) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            path = safe_member(info.filename)
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ValueError(f"source-delivery symlink is forbidden: {info.filename}")
            relative = PurePosixPath(*path.parts[1:]) if len(path.parts) > 1 else path
            if any(part.casefold() in FORBIDDEN_PARTS for part in relative.parts):
                continue
            payload = archive.read(info.filename)
            if relative.suffix.casefold() == ".zip":
                if hashlib.sha256(payload).hexdigest() == runtime_sha256:
                    continue
                try:
                    with zipfile.ZipFile(io.BytesIO(payload)) as nested:
                        for nested_info in nested.infolist():
                            if nested_info.is_dir():
                                continue
                            nested_path = safe_member(nested_info.filename)
                            nested_mode = (nested_info.external_attr >> 16) & 0o170000
                            if nested_mode == stat.S_IFLNK:
                                raise ValueError(
                                    f"nested source-delivery symlink is forbidden: {nested_info.filename}"
                                )
                            nested_relative = (
                                PurePosixPath(*nested_path.parts[1:])
                                if len(nested_path.parts) > 1
                                else nested_path
                            )
                            preserve(
                                nested.read(nested_info.filename),
                                PurePosixPath("legacy-source")
                                / relative.stem
                                / nested_relative,
                            )
                except zipfile.BadZipFile:
                    pass
                continue
            preserve(payload, PurePosixPath("legacy-source") / relative)
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize a historical runtime ZIP into one v0.0.0.5 full-delivery ZIP without changing its product version or bytes."
    )
    parser.add_argument("runtime", type=Path)
    parser.add_argument("--team-card", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--source-delivery",
        type=Path,
        help="Optional historical outer delivery whose non-ZIP human/audit files are preserved under reports/legacy-source/.",
    )
    args = parser.parse_args()
    runtime = args.runtime.expanduser().resolve()
    info = inspect_runtime_zip(runtime)
    try:
        team_card = json.loads(args.team_card.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        parser.error(f"invalid --team-card: {exc}")
    with tempfile.TemporaryDirectory(prefix="persona-legacy-reports-") as temporary:
        reports: list[tuple[Path, str]] = []
        if args.source_delivery:
            try:
                reports = extract_source_reports(
                    args.source_delivery.expanduser().resolve(),
                    Path(temporary),
                    info["sha256"],
                )
            except (OSError, ValueError, zipfile.BadZipFile) as exc:
                parser.error(str(exc))
        try:
            result = build_full_delivery(
                runtime,
                args.output,
                team_card=team_card,
                audit=legacy_audit(runtime),
                reports=reports,
                delivery_contract_status="legacy-normalized-v0.0.0.5",
                created_at=info["artifact_created_at"],
                provenance_mode="legacy-normalization-preserved-runtime",
            )
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            parser.error(str(exc))
    result["runtime_bytes_preserved"] = True
    result["source_delivery_reports_preserved"] = len(reports)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
