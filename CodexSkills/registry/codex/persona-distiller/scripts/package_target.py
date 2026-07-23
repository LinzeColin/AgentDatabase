#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    atomic_write_json,
    ensure_dir,
    ensure_target,
    parse_frontmatter,
    read_jsonl,
    scan_secrets,
    sha256_file,
)
from delivery_builder import build_full_delivery  # noqa: E402
from persona_registry import BUILDER_VERSION, default_registry_root, next_product_version_for  # noqa: E402

CORE_FILES = [
    "SKILL.md",
    "README.md",
    "install.py",
    "install.sh",
    "install.ps1",
    "meta.json",
    "identity-catalog.json",
    "route-manifest.json",
    "facts.md",
    "cognitive-os.md",
    "decision-policy.md",
    "strategy.md",
    "capabilities.md",
    "work.md",
    "persona.md",
    "boundaries.md",
    "hypotheses.md",
    "divergence-map.md",
    "corrections/ACTIVE.md",
]
CORE_DIRS = ["agents", "identity-facets", "scenario-adapters", "scripts"]
TEAM_CARD_ARRAY_FIELDS = (
    "selection_reasons",
    "distillation_traits",
    "user_value",
    "application_scenarios",
    "key_capabilities",
    "hard_boundaries",
)
FIXED_ZIP_TIME = (2026, 7, 23, 0, 0, 0)


def copy_file(source: Path, destination: Path) -> None:
    ensure_dir(destination.parent)
    shutil.copy2(source, destination)


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    os.chmod(path, 0o600)


def package_timestamp(meta: dict[str, Any]) -> str:
    return str(meta.get("updated_at") or meta.get("created_at") or "2026-07-23T00:00:00Z")


def sanitized_meta(meta: dict[str, Any], product_version: str) -> dict[str, Any]:
    clean = dict(meta)
    for key in ("consent_authority", "retention_policy", "last_rollback"):
        clean.pop(key, None)
    clean["builder_version"] = BUILDER_VERSION
    clean["product_version"] = product_version
    clean["runtime_invocation_versioning"] = False
    clean["packaged_at"] = package_timestamp(meta)
    clean["package_mode"] = "runtime"
    return clean


def sanitized_sources(target: Path) -> list[dict[str, Any]]:
    meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))
    private = meta.get("subject_origin") in {"private", "self"}
    result = []
    for record in read_jsonl(target / "evidence" / "source-ledger.jsonl"):
        clean = dict(record)
        for key in (
            "local_path",
            "normalized_path",
            "redactions",
            "original_name",
            "abstract",
            "locator",
        ):
            clean.pop(key, None)
        if private:
            clean["url"] = None
        result.append(clean)
    return result


def deterministic_zip(staging: Path, output: Path) -> None:
    ensure_dir(output.parent)
    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in sorted(item for item in staging.rglob("*") if item.is_file()):
            relative = path.relative_to(staging.parent).as_posix()
            info = zipfile.ZipInfo(relative, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if path.suffix in {".py", ".sh"} or path.name == "install.py" else 0o644
            info.external_attr = (mode & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes())


def validate_team_card(
    target: Path,
    meta: dict[str, Any],
    product_version: str,
) -> dict[str, Any]:
    path = target / "team-card.json"
    try:
        card = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"valid team-card.json is required: {exc}") from exc
    if not isinstance(card, dict):
        raise ValueError("team-card.json must contain an object")
    if card.get("readiness") != "ready":
        raise ValueError("team-card readiness must be ready before packaging")
    if not isinstance(card.get("research_cutoff"), str) or card["research_cutoff"] in {
        "",
        "unknown",
        "not-yet-established",
    }:
        raise ValueError("team-card requires a real research_cutoff")
    for field in TEAM_CARD_ARRAY_FIELDS:
        values = card.get(field)
        if (
            not isinstance(values, list)
            or not values
            or any(
                not isinstance(value, str)
                or not value.strip()
                or "replace-with-" in value
                for value in values
            )
        ):
            raise ValueError(f"team-card {field} must be fully populated")
    card["canonical_name"] = meta["name"]
    card["subject_slug"] = meta["slug"]
    card["latest_product_version"] = product_version
    return card


def run_quality_gate(target: Path, *, skip: bool) -> dict[str, Any]:
    if skip:
        return {
            "passed": False,
            "phase": "release",
            "strict": False,
            "profile": "unknown",
            "checks": [],
            "errors": [],
            "warnings": ["quality gate skipped by explicit flag"],
            "metrics": {},
        }
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parent / "quality_check.py"),
            str(target),
            "--phase",
            "release",
            "--strict",
        ],
        text=True,
        capture_output=True,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "strict release quality gate returned invalid JSON: "
            + (completed.stderr.strip() or completed.stdout[-2000:])
        ) from exc
    if completed.returncode != 0 or not payload.get("passed"):
        raise ValueError(
            "strict release quality gate failed: "
            + json.dumps(payload.get("errors", []), ensure_ascii=False)
        )
    return payload


def audit_payloads(
    target: Path,
    meta: dict[str, Any],
    quality: dict[str, Any],
    runtime_zip: Path,
) -> dict[str, dict[str, Any]]:
    timestamp = package_timestamp(meta)
    metrics = dict(quality.get("metrics") or {})
    source_records = read_jsonl(target / "evidence" / "source-ledger.jsonl")
    train = [record for record in source_records if record.get("split") != "holdout"]
    holdout = [record for record in source_records if record.get("split") == "holdout"]
    rights_counts = collections.Counter(
        str(record.get("rights") or "unknown") for record in source_records
    )
    lane_counts = metrics.get("lane_source_counts") or {}
    coverage_path = target / "research" / "coverage-map.json"
    if coverage_path.is_file():
        try:
            coverage_details = json.loads(coverage_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            coverage_details = {}
    else:
        coverage_details = {}
    cases_path = target / "evals" / "cases.jsonl"
    results_path = target / "evals" / "results.jsonl"
    frozen_outputs = {
        relative: {
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for relative, path in (
            ("evals/cases.jsonl", cases_path),
            ("evals/results.jsonl", results_path),
        )
        if path.is_file()
    }
    quality_passed = bool(quality.get("passed"))
    review_independence = str(
        meta.get("evaluation_independence")
        or "serialized-rubric-passes-not-independent-external-agents"
    )
    return {
        "verification.json": {
            "schema_version": "1.0",
            "status": "passed" if quality_passed else "skipped-quality-gate",
            "generated_at": timestamp,
            "checks": {
                "strict_release_quality": quality_passed,
                "runtime_integrity": True,
                "runtime_history_reset": True,
                "single_outer_archive": True,
                "sidecars_emitted": False,
                "secret_findings": metrics.get("secret_findings", 0),
            },
            "quality_errors": quality.get("errors", []),
            "quality_warnings": quality.get("warnings", []),
            "runtime_sha256": sha256_file(runtime_zip),
        },
        "provenance.json": {
            "schema_version": "1.0",
            "status": "passed" if source_records else "not-available-in-source-artifact",
            "generated_at": timestamp,
            "builder": "persona-distiller",
            "builder_version": BUILDER_VERSION,
            "subject_origin": meta.get("subject_origin"),
            "research_cutoff": meta.get("research_cutoff"),
            "source_record_counts": {
                "total": len(source_records),
                "train": len(train),
                "holdout": len(holdout),
            },
            "rights_summary": dict(sorted(rights_counts.items())),
            "private_paths_included": False,
            "source_bodies_included": False,
        },
        "source-coverage.json": {
            "schema_version": "1.0",
            "status": "passed" if len(lane_counts) >= 6 else "provisional",
            "generated_at": timestamp,
            "research_cutoff": meta.get("research_cutoff"),
            "lane_source_counts": lane_counts,
            "primary_ratio": metrics.get("primary_ratio"),
            "sources_total": metrics.get("sources_total", len(source_records)),
            "remaining_gaps": coverage_details.get("remaining_gaps", []),
            "bias_controls": coverage_details.get("anti_selection_bias_controls", []),
            "details": coverage_details,
            "claim": "coverage of the defined source universe; not proof of all public or private sources",
        },
        "evaluation-summary.json": {
            "schema_version": "1.0",
            "status": "passed" if quality_passed else "not-run",
            "generated_at": timestamp,
            "profile": quality.get("profile"),
            "suite_counts": metrics.get("eval_suite_counts", {}),
            "candidate_overall": metrics.get("candidate_overall"),
            "baseline_overall": metrics.get("baseline_overall"),
            "candidate_baseline_delta": metrics.get("candidate_baseline_delta"),
            "critical_failures": [
                error
                for error in quality.get("errors", [])
                if "critical" in json.dumps(error, ensure_ascii=False).casefold()
            ],
            "frozen_output_hashes": frozen_outputs,
            "independence": review_independence,
        },
        "review-record.json": {
            "schema_version": "1.0",
            "status": (
                "passed-with-independent-agents"
                if "independent-external" in review_independence
                else "passed-with-serialized-isolation"
            )
            if quality_passed
            else "not-run",
            "generated_at": timestamp,
            "roles": [
                "researcher",
                "builder",
                "generator",
                "counterevidence-analyst",
                "independent-reviewer",
                "decision-judge",
            ],
            "independence": review_independence,
            "same_context_roleplay_claimed_as_independent": False,
            "verdict": "release" if quality_passed else "not-evaluated",
        },
    }


def parse_reports(values: list[str]) -> list[tuple[Path, str]]:
    reports: list[tuple[Path, str]] = []
    for value in values:
        source_text, separator, relative = value.partition("=")
        source = Path(source_text)
        reports.append((source, relative if separator else source.name))
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build exactly one complete installable persona delivery ZIP."
    )
    parser.add_argument("target", type=Path)
    parser.add_argument("--output", type=Path, default=Path("./dist"))
    parser.add_argument("--registry-root", type=Path, default=default_registry_root())
    parser.add_argument(
        "--product-version",
        help="Optional assertion; must equal the registry-derived next product version.",
    )
    parser.add_argument(
        "--skip-quality",
        action="store_true",
        help="Development-only; the resulting audit records a skipped gate and is not release-ready.",
    )
    parser.add_argument(
        "--include-report",
        action="append",
        default=[],
        metavar="PATH[=RELATIVE_NAME]",
        help="Optional human-readable report to embed under reports/.",
    )
    parser.add_argument(
        "--include-audit-summary",
        action="store_true",
        help="Compatibility no-op: v0.0.0.5 always embeds the full audit summary.",
    )
    parser.add_argument("--allow-secret-pattern", action="store_true")
    args = parser.parse_args()
    target = args.target.expanduser().resolve()
    meta = ensure_target(target)
    frontmatter, _ = parse_frontmatter(target / "SKILL.md")
    if set(frontmatter) != {"name", "description"}:
        parser.error("target SKILL.md frontmatter must contain only name and description")
    if frontmatter["name"] != target.name:
        parser.error("target SKILL.md name must match directory")
    if str(meta.get("status", "")).startswith("blocked"):
        parser.error(f"target status blocks release: {meta.get('status')}")
    try:
        quality = run_quality_gate(target, skip=args.skip_quality)
    except ValueError as exc:
        parser.error(str(exc))
    product_version = next_product_version_for(
        str(meta.get("name", "")),
        str(meta.get("subject_origin", "")),
        args.registry_root,
    )
    if args.product_version and args.product_version != product_version:
        parser.error(
            f"--product-version {args.product_version} is not the next available version "
            f"for this person; expected {product_version}"
        )
    try:
        team_card = validate_team_card(target, meta, product_version)
    except ValueError as exc:
        parser.error(str(exc))
    with tempfile.TemporaryDirectory(prefix="persona-target-package-") as temporary:
        temporary_root = Path(temporary)
        runtime_staging = temporary_root / target.name
        runtime_staging.mkdir()
        for relative in CORE_FILES:
            if (target / relative).is_file():
                copy_file(target / relative, runtime_staging / relative)
        for relative in CORE_DIRS:
            if (target / relative).is_dir():
                shutil.copytree(
                    target / relative,
                    runtime_staging / relative,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                )
        atomic_write_json(
            runtime_staging / "meta.json",
            sanitized_meta(meta, product_version),
            mode=0o600,
        )
        write_jsonl(
            runtime_staging / "evidence" / "claims.jsonl",
            read_jsonl(target / "evidence" / "claims.jsonl"),
        )
        write_jsonl(
            runtime_staging / "evidence" / "source-ledger.jsonl",
            sanitized_sources(target),
        )
        write_jsonl(runtime_staging / "corrections" / "corrections.jsonl", [])
        write_jsonl(runtime_staging / "memory" / "episodic.jsonl", [])
        for relative in (
            "memory/user-overlay.md",
            "memory/procedural.md",
            "memory/promotion-queue.md",
        ):
            if (target / relative).is_file():
                copy_file(target / relative, runtime_staging / relative)
        write_jsonl(runtime_staging / "runtime" / "invocations.jsonl", [])
        findings = scan_secrets(
            runtime_staging,
            exclude_dirs={".git", "__pycache__"},
        )
        if findings and not args.allow_secret_pattern:
            parser.error(
                "secret-like patterns detected: "
                + json.dumps(findings[:10], ensure_ascii=False)
            )
        records = []
        for path in sorted(item for item in runtime_staging.rglob("*") if item.is_file()):
            if path.name in {"checksums.sha256", "PACKAGE_MANIFEST.json"}:
                continue
            records.append(
                {
                    "path": path.relative_to(runtime_staging).as_posix(),
                    "sha256": sha256_file(path),
                    "size": path.stat().st_size,
                }
            )
        checksums = "".join(
            f"{item['sha256']}  {item['path']}\n" for item in records
        )
        (runtime_staging / "checksums.sha256").write_text(checksums, encoding="utf-8")
        manifest = {
            "schema_version": "2.0",
            "name": target.name,
            "target_name": meta.get("name"),
            "builder": "persona-distiller",
            "builder_version": BUILDER_VERSION,
            "product_version": product_version,
            "model_version": meta.get("model_version"),
            "created_at": package_timestamp(meta),
            "top_level_count": 1,
            "privacy": {
                "raw_included": False,
                "holdout_included": False,
                "private_source_bodies_included": False,
                "runtime_history_reset": True,
            },
            "files": records,
        }
        atomic_write_json(runtime_staging / "PACKAGE_MANIFEST.json", manifest)
        runtime_zip = temporary_root / (
            f"{target.name}-persona-skill-v{product_version}.zip"
        )
        deterministic_zip(runtime_staging, runtime_zip)
        audit = audit_payloads(target, meta, quality, runtime_zip)
        output = args.output.expanduser().resolve()
        if output.suffix.casefold() != ".zip":
            output.mkdir(parents=True, exist_ok=True)
            output = output / (
                f"{target.name}-persona-distillation-delivery-v"
                f"{product_version}.zip"
            )
        try:
            result = build_full_delivery(
                runtime_zip,
                output,
                team_card=team_card,
                audit=audit,
                reports=parse_reports(args.include_report),
                delivery_contract_status="native-v0.0.0.5",
                created_at=package_timestamp(meta),
                provenance_mode="native-build",
            )
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            parser.error(str(exc))
    result.update(
        {
            "product_version_consumed": False,
            "runtime_records_reset": True,
            "runtime_invocation_versioning": False,
            "registration_required": True,
            "register_command": f"python3 scripts/register_persona.py {output}",
        }
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
