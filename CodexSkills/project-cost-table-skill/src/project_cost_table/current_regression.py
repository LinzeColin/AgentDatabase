"""Private R11 preparation and exact expected-block harness.

The production current-source module does not import this file.  This module is
allowed to read the sealed private current snapshot to prepare a private,
gitignored expectation before the production command runs.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import stat
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

import yaml

from .current_reconstruction import (
    CURRENT_BASIS_IDS,
    CURRENT_METRICS,
    PROHIBITED_CALCULATE_SLOT_IDS,
    CurrentReconstructionError,
    load_current_source_contract,
    metadata_fingerprint,
    recompute_current_request_hash,
)
from .generation import verify_output_index, verify_run_seal
from .inventory import InventoryEntry, build_private_full_inventory, match_inventory_entries
from .paths import PathSafetyError, atomic_output_directory


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CONTROL_FILES = frozenset({"OUTPUT_INDEX.md", "output_index.json", "run_seal.sha256"})
R11_EXPECTED_BLOCKERS = tuple(
    sorted(
        (
            "ACCOUNTING_BASIS_POLICY_MISSING",
            "CAPITAL_INTEREST_POLICY_MISSING",
            "CURRENT_INPUT_MANIFEST_V3_MISSING",
            "FULLY_LOADED_PAYROLL_POLICY_MISSING",
            "KINGDEE_READER_PROFILE_MISSING",
            "PAYMENT_PROJECT_MAPPING_CONFLICT",
            "PAYROLL_AND_TIME_SOURCE_MISSING",
            "PROJECT_IDENTITY_EVIDENCE_CONFLICT",
            "PROJECT_TAX_POLICY_OR_DIRECT_LEDGER_MISSING",
        )
    )
)


class CurrentRegressionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


@dataclass(frozen=True)
class PreparedCurrentRegression:
    output_dir: Path
    current_source_contract: Path
    current_source_contract_sha256: str
    expected_block_contract: Path
    expected_block_contract_sha256: str
    source_drift_review: Path
    output_index_md: Path
    run_seal: Path

    def locator_text(self) -> str:
        return "\n".join(
            (
                "RESULT_STATUS: CURRENT_REGRESSION_BINDING_PREPARED",
                "OUTPUT_DIR: %s" % self.output_dir,
                "PRIMARY_OUTPUT: %s" % self.current_source_contract,
                "OUTPUT_INDEX: %s" % self.output_index_md,
                "NEXT_STEP: 先直接运行生产命令确认 exit 3，再由独立 harness 精确核对密封 blocker 合同。",
            )
        )


@dataclass(frozen=True)
class ExpectedBlockContract:
    expectation_id: str
    current_source_contract_sha256: str
    expected_production_exit_code: int
    expected_status_planes: Mapping[str, str]
    expected_blocker_codes: Tuple[str, ...]
    expected_project_count: int
    calculate_source_boundary: Mapping[str, bool]
    content_sha256: str


@dataclass(frozen=True)
class PublishedExpectedBlockValidation:
    output_dir: Path
    primary_output: Path
    output_index_md: Path
    run_seal: Path
    passed: bool

    def locator_text(self) -> str:
        return "\n".join(
            (
                "RESULT_STATUS: %s" % ("EXPECTED_BLOCKED" if self.passed else "FAILED"),
                "OUTPUT_DIR: %s" % self.output_dir,
                "PRIMARY_OUTPUT: %s" % self.primary_output,
                "OUTPUT_INDEX: %s" % self.output_index_md,
                "NEXT_STEP: %s"
                % (
                    "R11 精确阻断验收已通过；继续保持 NO_GO_PRODUCTION，进入下一 Run 前先复核证据。"
                    if self.passed
                    else "查看 validation_errors，修复真实漂移；不得改写预期值、隐藏 blocker 或注入回放数据。"
                ),
            )
        )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(encoded)


def _write_exclusive(path: Path, data: bytes) -> None:
    with Path(path).open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _safe_manifest_relative(value: str) -> Path:
    if not value or "\x00" in value or "\\" in value:
        raise CurrentRegressionError("TASK_PACK_MANIFEST_PATH", "Task Pack manifest contains an unsafe path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise CurrentRegressionError("TASK_PACK_MANIFEST_PATH", "Task Pack manifest contains an unsafe path")
    return Path(*pure.parts)


def verify_task_pack_manifest(task_pack_root: Path) -> Tuple[str, int]:
    root = Path(task_pack_root)
    manifest = root / "manifest.sha256"
    try:
        metadata = manifest.lstat()
    except OSError as exc:
        raise CurrentRegressionError("TASK_PACK_MANIFEST_MISSING", "Task Pack manifest is unavailable") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise CurrentRegressionError("TASK_PACK_MANIFEST_UNSAFE", "Task Pack manifest must be a single-link regular file")
    seen = set()
    try:
        lines = manifest.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as exc:
        raise CurrentRegressionError("TASK_PACK_MANIFEST_UNREADABLE", "Task Pack manifest cannot be read") from exc
    if not lines:
        raise CurrentRegressionError("TASK_PACK_MANIFEST_EMPTY", "Task Pack manifest cannot be empty")
    for line in lines:
        try:
            digest, relative = line.split("  ", 1)
        except ValueError as exc:
            raise CurrentRegressionError("TASK_PACK_MANIFEST_FORMAT", "Task Pack manifest line is malformed") from exc
        if not SHA256_RE.fullmatch(digest):
            raise CurrentRegressionError("TASK_PACK_MANIFEST_FORMAT", "Task Pack manifest digest is malformed")
        relative_path = _safe_manifest_relative(relative)
        if relative in seen:
            raise CurrentRegressionError("TASK_PACK_MANIFEST_DUPLICATE", "Task Pack manifest path is duplicated")
        seen.add(relative)
        path = root / relative_path
        try:
            file_metadata = path.lstat()
        except OSError as exc:
            raise CurrentRegressionError("TASK_PACK_FILE_MISSING", "Task Pack file listed by manifest is unavailable") from exc
        if stat.S_ISLNK(file_metadata.st_mode) or not stat.S_ISREG(file_metadata.st_mode) or file_metadata.st_nlink != 1:
            raise CurrentRegressionError("TASK_PACK_FILE_UNSAFE", "Task Pack file listed by manifest is unsafe")
        if _sha256_file(path) != digest:
            raise CurrentRegressionError("TASK_PACK_HASH_DRIFT", "Task Pack file digest differs from its sealed manifest")
    return _sha256_file(manifest), len(lines)


def _load_yaml(path: Path) -> Mapping[str, Any]:
    try:
        value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise CurrentRegressionError("PRIVATE_SEED_PARSE", "sealed private YAML seed cannot be parsed") from exc
    if not isinstance(value, dict):
        raise CurrentRegressionError("PRIVATE_SEED_SCHEMA", "sealed private YAML seed must be a mapping")
    return value


def _load_json(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CurrentRegressionError("PRIVATE_SEED_PARSE", "sealed private JSON seed cannot be parsed") from exc
    if not isinstance(value, dict):
        raise CurrentRegressionError("PRIVATE_SEED_SCHEMA", "sealed private JSON seed must be a mapping")
    return value


def _pattern_matches(relative_path: str, pattern: str) -> bool:
    if fnmatch.fnmatchcase(relative_path, pattern):
        return True
    if pattern.startswith("**/"):
        return fnmatch.fnmatchcase(relative_path, pattern[3:])
    return False


def _digest_counter(rows: Iterable[Mapping[str, Any]]) -> Counter:
    counter: Counter = Counter()
    for row in rows:
        digest = row.get("sha256")
        size = row.get("size_bytes")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest) or type(size) is not int or size < 0:
            raise CurrentRegressionError("SOURCE_SNAPSHOT_SCHEMA", "source hash snapshot record is invalid")
        counter[(digest, size)] += 1
    return counter


def _inventory_rows(entries: Sequence[InventoryEntry]) -> Tuple[Mapping[str, Any], ...]:
    rows = []
    for entry in entries:
        if entry.status != "VERIFIED" or entry.sha256 is None:
            raise CurrentRegressionError("CURRENT_SOURCE_UNSAFE", "current raw inventory contains an unsafe or unhashable entry")
        rows.append(
            {
                "relative_path": entry.relative_path,
                "sha256": entry.sha256,
                "size_bytes": entry.identity.size_bytes,
                "source_id": entry.source_id,
            }
        )
    return tuple(rows)


def _counter_fingerprint(counter: Counter) -> str:
    rows = [
        {"sha256": digest, "size_bytes": size, "occurrences": count}
        for (digest, size), count in sorted(counter.items())
    ]
    return _stable_hash(rows)


def _output_controls(directory: Path, final_root: Path, *, result_status: str, primary_name: str, next_step: str) -> None:
    business_files = sorted(
        (path for path in directory.iterdir() if path.is_file() and path.name not in CONTROL_FILES),
        key=lambda path: path.name,
    )
    md_lines = [
        "# Current regression output index",
        "",
        "RESULT_STATUS: `%s`" % result_status,
        "",
        "OUTPUT_DIR: `%s`" % final_root,
        "",
        "PRIMARY_OUTPUT: `%s`" % (final_root / primary_name),
        "",
        "OUTPUT_INDEX: `%s`" % (final_root / "OUTPUT_INDEX.md"),
        "",
        "| Artifact | SHA256 | Absolute path |",
        "| --- | --- | --- |",
    ]
    files = []
    for path in business_files:
        digest = _sha256_file(path)
        md_lines.append("| `%s` | `%s` | `%s` |" % (path.name, digest, final_root / path.name))
        files.append({"path": str(final_root / path.name), "sha256": digest, "artifact_type": path.name})
    md_lines.extend(("", "NEXT_STEP: %s" % next_step))
    _write_exclusive(directory / "OUTPUT_INDEX.md", ("\n".join(md_lines) + "\n").encode("utf-8"))
    index_payload = {
        "schema_version": "kmfa.project_cost.current_regression_output_index.private.v1",
        "result_status": result_status,
        "output_dir": str(final_root),
        "primary_output": str(final_root / primary_name),
        "output_index": str(final_root / "OUTPUT_INDEX.md"),
        "seal_path": str(final_root / "run_seal.sha256"),
        "files": files,
        "next_step": next_step,
    }
    _write_exclusive(directory / "output_index.json", _json_bytes(index_payload))
    seal_lines = []
    for path in sorted((item for item in directory.iterdir() if item.is_file() and item.name != "run_seal.sha256"), key=lambda item: item.name):
        seal_lines.append("%s  %s" % (_sha256_file(path), path.name))
    _write_exclusive(directory / "run_seal.sha256", ("\n".join(seal_lines) + "\n").encode("ascii"))


def verify_regression_bundle(output_dir: Path) -> bool:
    root = Path(output_dir)
    seal = root / "run_seal.sha256"
    try:
        lines = seal.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError):
        return False
    expected = {path.name for path in root.iterdir() if path.is_file() and path.name != seal.name}
    observed = set()
    for line in lines:
        try:
            digest, name = line.split("  ", 1)
        except ValueError:
            return False
        if not SHA256_RE.fullmatch(digest) or Path(name).name != name or name in observed:
            return False
        path = root / name
        if not path.is_file() or _sha256_file(path) != digest:
            return False
        observed.add(name)
    return observed == expected


def _derive_private_requirements(
    *,
    locator_seed: Mapping[str, Any],
    alias_seed: Mapping[str, Any],
    formula_seed: Mapping[str, Any],
    validation_summary: Mapping[str, Any],
    current_slot_counts: Mapping[str, int],
) -> Tuple[Mapping[str, Optional[str]], ...]:
    formulas = formula_seed.get("formulas")
    redcircle_blockers = validation_summary.get("redcircle_blockers")
    if not isinstance(formulas, dict) or not isinstance(redcircle_blockers, list):
        raise CurrentRegressionError("PRIVATE_SEED_SCHEMA", "formula or validation private seed fields drifted")
    requirements = (
        {
            "requirement_id": "CURRENT_INPUT_MANIFEST_V3",
            "observed_status": "MISSING" if locator_seed.get("schema_version") != "kmfa.project_cost.input_manifest.v3" else "PRESENT",
            "evidence_ref": "sealed-current-locator-seed",
        },
        {
            "requirement_id": "PROJECT_IDENTITY_EVIDENCE",
            "observed_status": "CONFLICT" if alias_seed.get("status") != "ACTIVE_GOVERNED_IDENTITY" else "PRESENT",
            "evidence_ref": "sealed-identity-seed-status",
        },
        {
            "requirement_id": "KINGDEE_READER_PROFILE",
            "observed_status": "MISSING",
            "evidence_ref": "sealed-current-package-profile-inventory",
        },
        {
            "requirement_id": "ACCOUNTING_BASIS_POLICY",
            "observed_status": "MISSING",
            "evidence_ref": "sealed-current-package-policy-inventory",
        },
        {
            "requirement_id": "PAYROLL_AND_TIME_SOURCE",
            "observed_status": "MISSING" if current_slot_counts.get("payroll_and_time", 0) == 0 else "PRESENT",
            "evidence_ref": "current-slot-count:payroll_and_time",
        },
        {
            "requirement_id": "FULLY_LOADED_PAYROLL_POLICY",
            "observed_status": "MISSING"
            if not isinstance(formulas.get("payroll_self_labor"), dict)
            or formulas["payroll_self_labor"].get("status") != "ACTIVE"
            else "PRESENT",
            "evidence_ref": "sealed-formula-profile:payroll",
        },
        {
            "requirement_id": "PROJECT_TAX_POLICY_OR_DIRECT_LEDGER",
            "observed_status": "MISSING"
            if not isinstance(formulas.get("project_tax"), dict)
            or formulas["project_tax"].get("status") != "ACTIVE"
            else "PRESENT",
            "evidence_ref": "sealed-formula-profile:project-tax",
        },
        {
            "requirement_id": "CAPITAL_INTEREST_POLICY",
            "observed_status": "MISSING"
            if not isinstance(formulas.get("capital_occupation_interest"), dict)
            or formulas["capital_occupation_interest"].get("status") != "ACTIVE"
            else "PRESENT",
            "evidence_ref": "sealed-formula-profile:capital-interest",
        },
        {
            "requirement_id": "PAYMENT_PROJECT_MAPPING",
            "observed_status": "CONFLICT"
            if "payment_has_no_stable_project_key" in redcircle_blockers
            else "PRESENT",
            "evidence_ref": "sealed-redcircle-mapping-status",
        },
    )
    return tuple(requirements)


def prepare_current_regression_bundle(
    *,
    task_pack_root: Path,
    input_root: Path,
    output_dir: Path,
    contract_id: str,
    as_of: str,
) -> PreparedCurrentRegression:
    start = time.perf_counter()
    task_pack = Path(task_pack_root).resolve(strict=True)
    raw_root = Path(input_root).resolve(strict=True)
    final_root = Path(output_dir)
    if not final_root.is_absolute() or final_root.exists() or not final_root.parent.is_dir():
        raise CurrentRegressionError("BINDING_OUTPUT_INVALID", "binding output must be a new absolute path")
    task_manifest_sha, task_manifest_record_count = verify_task_pack_manifest(task_pack)
    seed_root = task_pack / "private_seed"
    locator_seed = _load_yaml(seed_root / "input_manifest.current.private.yml")
    alias_seed = _load_yaml(seed_root / "project_aliases.reference.private.yml")
    formula_seed = _load_yaml(seed_root / "formula_profile.reference_observed.private.yml")
    validation_summary = _load_json(seed_root / "current_snapshot" / "validation_summary.json")
    source_snapshot_path = seed_root / "current_snapshot" / "source_hash_manifest.json"
    source_snapshot = _load_json(source_snapshot_path)
    source_slots = locator_seed.get("source_slots")
    baseline_rows = source_snapshot.get("files")
    if locator_seed.get("schema_version") != "kmfa.project_cost.private_source_locator_seed.v1" or not isinstance(source_slots, dict):
        raise CurrentRegressionError("LOCATOR_SEED_SCHEMA", "private locator seed schema drifted")
    if source_snapshot.get("schema_version") != "kmfa.project_cost.source_inventory.v1" or not isinstance(baseline_rows, list):
        raise CurrentRegressionError("SOURCE_SNAPSHOT_SCHEMA", "private source snapshot schema drifted")

    current_entries = build_private_full_inventory(raw_root)
    current_rows = _inventory_rows(current_entries)
    baseline_counter = _digest_counter(baseline_rows)
    current_counter = _digest_counter(current_rows)
    common_counter = baseline_counter & current_counter
    missing_counter = baseline_counter - current_counter
    new_counter = current_counter - baseline_counter
    slot_reviews = []
    current_slot_counts: Dict[str, int] = {}
    in_scope_slot_drift = []
    selected_sources = []
    for slot_id, body in sorted(source_slots.items()):
        if not isinstance(body, dict) or not isinstance(body.get("private_patterns"), list):
            raise CurrentRegressionError("LOCATOR_SEED_SCHEMA", "source slot pattern list drifted")
        patterns = tuple(body.get("private_patterns", ()))
        baseline_candidates = [
            row
            for row in baseline_rows
            if isinstance(row, dict)
            and isinstance(row.get("relative_path"), str)
            and any(_pattern_matches(row["relative_path"], pattern) for pattern in patterns)
        ]
        current_candidates = match_inventory_entries(current_entries, patterns)
        current_slot_counts[slot_id] = len(current_candidates)
        baseline_slot_counter = _digest_counter(baseline_candidates)
        current_slot_counter = _digest_counter(
            {
                "sha256": item.sha256,
                "size_bytes": item.identity.size_bytes,
            }
            for item in current_candidates
        )
        exact = baseline_slot_counter == current_slot_counter
        if not exact:
            in_scope_slot_drift.append(slot_id)
        slot_reviews.append(
            {
                "slot_id": slot_id,
                "baseline_candidate_count": sum(baseline_slot_counter.values()),
                "current_candidate_count": sum(current_slot_counter.values()),
                "candidate_digest_multiset_exact": exact,
                "baseline_candidate_fingerprint": _counter_fingerprint(baseline_slot_counter),
                "current_candidate_fingerprint": _counter_fingerprint(current_slot_counter),
            }
        )
        if slot_id in PROHIBITED_CALCULATE_SLOT_IDS:
            continue
        for item in current_candidates:
            if item.sha256 is None:
                raise CurrentRegressionError("CURRENT_SOURCE_UNHASHED", "selected current source has no full digest")
            selected_sources.append(
                {
                    "slot_id": slot_id,
                    "source_id": item.source_id,
                    "private_relative_path": item.relative_path,
                    "sha256": item.sha256,
                }
            )
    if in_scope_slot_drift:
        raise CurrentRegressionError(
            "CURRENT_IN_SCOPE_SOURCE_DRIFT",
            "one or more governed source-slot digest sets changed; review is required before preparing R11",
        )
    if not missing_counter and not new_counter:
        drift_classification = "NO_SOURCE_DRIFT"
    else:
        drift_classification = "OUT_OF_SCOPE_INVENTORY_DRIFT"
    if drift_classification != "OUT_OF_SCOPE_INVENTORY_DRIFT":
        raise CurrentRegressionError("R11_DRIFT_EXPECTATION_CHANGED", "R11 expects reviewed out-of-scope inventory drift")
    drift_payload = {
        "schema_version": "kmfa.project_cost.source_drift_review.private.v1",
        "classification": "PRIVATE_RUNTIME_DO_NOT_COMMIT",
        "baseline_source_snapshot_sha256": _sha256_file(source_snapshot_path),
        "baseline_file_count": sum(baseline_counter.values()),
        "current_file_count": sum(current_counter.values()),
        "exact_digest_match_count": sum(common_counter.values()),
        "baseline_missing_digest_count": sum(missing_counter.values()),
        "current_new_digest_count": sum(new_counter.values()),
        "slot_reviews": slot_reviews,
        "in_scope_slot_drift_count": 0,
        "drift_classification": drift_classification,
        "review_disposition": "ACCEPT_FOR_R11_WITH_CURRENT_METADATA_AND_SELECTED_DIGEST_LOCKS",
        "snapshot_overwritten": False,
        "baseline_global_digest_fingerprint": _counter_fingerprint(baseline_counter),
        "current_global_digest_fingerprint": _counter_fingerprint(current_counter),
    }
    drift_bytes = _json_bytes(drift_payload)
    drift_sha = _sha256_bytes(drift_bytes)
    project_count = validation_summary.get("reference_project_count")
    if type(project_count) is not int or project_count <= 0:
        raise CurrentRegressionError("PRIVATE_VALIDATION_SCHEMA", "private current project count is invalid")
    requirements = _derive_private_requirements(
        locator_seed=locator_seed,
        alias_seed=alias_seed,
        formula_seed=formula_seed,
        validation_summary=validation_summary,
        current_slot_counts=current_slot_counts,
    )
    observed_expected = []
    for item in requirements:
        requirement_id = item["requirement_id"]
        status_value = item["observed_status"]
        if status_value == "PRESENT":
            continue
        expected_map = {
            ("CURRENT_INPUT_MANIFEST_V3", "MISSING"): "CURRENT_INPUT_MANIFEST_V3_MISSING",
            ("PROJECT_IDENTITY_EVIDENCE", "CONFLICT"): "PROJECT_IDENTITY_EVIDENCE_CONFLICT",
            ("KINGDEE_READER_PROFILE", "MISSING"): "KINGDEE_READER_PROFILE_MISSING",
            ("ACCOUNTING_BASIS_POLICY", "MISSING"): "ACCOUNTING_BASIS_POLICY_MISSING",
            ("PAYROLL_AND_TIME_SOURCE", "MISSING"): "PAYROLL_AND_TIME_SOURCE_MISSING",
            ("FULLY_LOADED_PAYROLL_POLICY", "MISSING"): "FULLY_LOADED_PAYROLL_POLICY_MISSING",
            ("PROJECT_TAX_POLICY_OR_DIRECT_LEDGER", "MISSING"): "PROJECT_TAX_POLICY_OR_DIRECT_LEDGER_MISSING",
            ("CAPITAL_INTEREST_POLICY", "MISSING"): "CAPITAL_INTEREST_POLICY_MISSING",
            ("PAYMENT_PROJECT_MAPPING", "CONFLICT"): "PAYMENT_PROJECT_MAPPING_CONFLICT",
        }
        blocker = expected_map.get((requirement_id, status_value))
        if blocker is None:
            raise CurrentRegressionError("PRIVATE_EXPECTATION_DRIFT", "private requirement status no longer matches reviewed R11 expectation")
        observed_expected.append(blocker)
    if tuple(sorted(observed_expected)) != R11_EXPECTED_BLOCKERS:
        raise CurrentRegressionError("PRIVATE_EXPECTATION_DRIFT", "reviewed R11 blocker set changed")

    contract_payload = {
        "schema_version": "kmfa.project_cost.current_source_contract.private.v1",
        "classification": "PRIVATE_RUNTIME_DO_NOT_COMMIT",
        "contract_id": contract_id,
        "input_root": str(raw_root),
        "as_of": as_of,
        "scope": {
            "project_count": project_count,
            "requested_metrics": list(CURRENT_METRICS),
            "requested_basis_ids": list(CURRENT_BASIS_IDS),
        },
        "source_snapshot": {
            "metadata_fingerprint": metadata_fingerprint(current_entries),
            "entry_count": len(current_entries),
            "total_size_bytes": sum(item.identity.size_bytes for item in current_entries),
            "unsafe_entry_count": sum(item.status == "UNSAFE" for item in current_entries),
            "task_pack_manifest_sha256": task_manifest_sha,
            "drift_review_sha256": drift_sha,
            "drift_classification": "OUT_OF_SCOPE_INVENTORY_DRIFT_REVIEWED",
            "snapshot_overwritten": False,
        },
        "selected_sources": sorted(selected_sources, key=lambda item: (item["slot_id"], item["source_id"])),
        "evidence_requirements": sorted(requirements, key=lambda item: str(item["requirement_id"])),
        "calculate_source_boundary": {
            "baseline_values_allowed": False,
            "report_line_items_allowed": False,
            "replay_adapters_allowed": False,
        },
    }
    contract_bytes = _json_bytes(contract_payload)
    contract_sha = _sha256_bytes(contract_bytes)
    expected_payload = {
        "schema_version": "kmfa.project_cost.expected_block_contract.private.v1",
        "classification": "PRIVATE_RUNTIME_DO_NOT_COMMIT",
        "expectation_id": contract_id + "-expected-block",
        "current_source_contract_sha256": contract_sha,
        "expected_production_exit_code": 3,
        "expected_status_planes": {
            "execution_status": "NEEDS_USER_INPUT",
            "input_readiness_status": "BLOCKED_NON_WAIVABLE",
            "calculation_status": "BLOCKED_SOURCE",
            "generation_status": "BLOCKED_DIAGNOSTICS_GENERATED",
        },
        "expected_blocker_codes": list(R11_EXPECTED_BLOCKERS),
        "expected_project_count": project_count,
        "calculate_source_boundary": {
            "baseline_values_allowed": False,
            "report_line_items_allowed": False,
            "replay_adapters_allowed": False,
        },
        "expectation_frozen_before_production": True,
    }
    expected_bytes = _json_bytes(expected_payload)
    expected_sha = _sha256_bytes(expected_bytes)
    import_manifest = {
        "schema_version": "kmfa.project_cost.current_regression_import.private.v1",
        "classification": "PRIVATE_RUNTIME_DO_NOT_COMMIT",
        "prepared_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "task_pack_manifest_sha256": task_manifest_sha,
        "task_pack_manifest_record_count": task_manifest_record_count,
        "current_source_contract_sha256": contract_sha,
        "expected_block_contract_sha256": expected_sha,
        "source_drift_review_sha256": drift_sha,
        "selected_calculate_source_count": len(selected_sources),
        "project_count": project_count,
        "private_values_copied": False,
        "reference_baseline_imported": False,
        "snapshot_overwritten": False,
        "preparation_elapsed_ms": int((time.perf_counter() - start) * 1000),
    }
    try:
        with atomic_output_directory(final_root.parent, final_root.name) as temporary:
            _write_exclusive(temporary / "source_drift_review.json", drift_bytes)
            _write_exclusive(temporary / "current_source_contract.private.json", contract_bytes)
            _write_exclusive(temporary / "expected_block_contract.private.json", expected_bytes)
            _write_exclusive(temporary / "import_manifest.json", _json_bytes(import_manifest))
            _output_controls(
                temporary,
                final_root,
                result_status="CURRENT_REGRESSION_BINDING_PREPARED",
                primary_name="current_source_contract.private.json",
                next_step="先运行生产命令确认 exit 3；再运行独立 harness，比对预先密封的精确 blocker 集。",
            )
            if not verify_regression_bundle(temporary):
                raise CurrentRegressionError("BINDING_SEAL_VERIFY", "prepared binding seal failed before publish")
    except PathSafetyError as exc:
        raise CurrentRegressionError(exc.code, exc.message) from exc
    if not verify_regression_bundle(final_root):
        raise CurrentRegressionError("BINDING_PUBLISH_VERIFY", "published binding bundle failed detached-seal verification")
    return PreparedCurrentRegression(
        output_dir=final_root,
        current_source_contract=final_root / "current_source_contract.private.json",
        current_source_contract_sha256=contract_sha,
        expected_block_contract=final_root / "expected_block_contract.private.json",
        expected_block_contract_sha256=expected_sha,
        source_drift_review=final_root / "source_drift_review.json",
        output_index_md=final_root / "OUTPUT_INDEX.md",
        run_seal=final_root / "run_seal.sha256",
    )


def load_expected_block_contract(path: Path, expected_sha256: str) -> ExpectedBlockContract:
    value = Path(path)
    try:
        metadata = value.lstat()
        data = value.read_bytes()
    except OSError as exc:
        raise CurrentRegressionError("EXPECTED_CONTRACT_UNAVAILABLE", "expected-block contract is unavailable") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise CurrentRegressionError("EXPECTED_CONTRACT_UNSAFE", "expected-block contract must be a single-link regular file")
    if not SHA256_RE.fullmatch(expected_sha256) or _sha256_bytes(data) != expected_sha256:
        raise CurrentRegressionError("EXPECTED_CONTRACT_HASH_DRIFT", "expected-block contract differs from its pre-run seal")
    try:
        raw = json.loads(data)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CurrentRegressionError("EXPECTED_CONTRACT_PARSE", "expected-block contract is invalid JSON") from exc
    expected_keys = {
        "schema_version",
        "classification",
        "expectation_id",
        "current_source_contract_sha256",
        "expected_production_exit_code",
        "expected_status_planes",
        "expected_blocker_codes",
        "expected_project_count",
        "calculate_source_boundary",
        "expectation_frozen_before_production",
    }
    if not isinstance(raw, dict) or set(raw) != expected_keys:
        raise CurrentRegressionError("EXPECTED_CONTRACT_SCHEMA", "expected-block contract fields drifted")
    if raw.get("schema_version") != "kmfa.project_cost.expected_block_contract.private.v1" or raw.get("classification") != "PRIVATE_RUNTIME_DO_NOT_COMMIT":
        raise CurrentRegressionError("EXPECTED_CONTRACT_SCHEMA", "expected-block contract schema/classification is invalid")
    statuses = raw.get("expected_status_planes")
    expected_statuses = {
        "execution_status": "NEEDS_USER_INPUT",
        "input_readiness_status": "BLOCKED_NON_WAIVABLE",
        "calculation_status": "BLOCKED_SOURCE",
        "generation_status": "BLOCKED_DIAGNOSTICS_GENERATED",
    }
    boundary = raw.get("calculate_source_boundary")
    if (
        statuses != expected_statuses
        or not isinstance(boundary, dict)
        or any(value is not False for value in boundary.values())
    ):
        raise CurrentRegressionError("EXPECTED_CONTRACT_RELAXED", "expected status or calculate isolation was relaxed")
    blockers = raw.get("expected_blocker_codes")
    if not isinstance(blockers, list) or tuple(blockers) != R11_EXPECTED_BLOCKERS:
        raise CurrentRegressionError("EXPECTED_BLOCKER_SET_DRIFT", "expected-block contract does not match the reviewed R11 set")
    if raw.get("expected_production_exit_code") != 3 or raw.get("expectation_frozen_before_production") is not True:
        raise CurrentRegressionError("EXPECTED_CONTRACT_RELAXED", "production exit or pre-run freeze requirement was relaxed")
    source_sha = raw.get("current_source_contract_sha256")
    project_count = raw.get("expected_project_count")
    if not isinstance(source_sha, str) or not SHA256_RE.fullmatch(source_sha) or type(project_count) is not int or project_count <= 0:
        raise CurrentRegressionError("EXPECTED_CONTRACT_SCHEMA", "expected source binding or project count is invalid")
    return ExpectedBlockContract(
        expectation_id=str(raw.get("expectation_id")),
        current_source_contract_sha256=source_sha,
        expected_production_exit_code=3,
        expected_status_planes=dict(statuses),
        expected_blocker_codes=tuple(blockers),
        expected_project_count=project_count,
        calculate_source_boundary=dict(boundary),
        content_sha256=_sha256_bytes(data),
    )


def validate_current_expected_block(
    *,
    production_output_dir: Path,
    production_exit_code: int,
    input_root: Path,
    source_contract_path: Path,
    source_contract_sha256: str,
    expected_contract_path: Path,
    expected_contract_sha256: str,
) -> Mapping[str, Any]:
    start = time.perf_counter()
    production = Path(production_output_dir)
    errors = []
    try:
        expected = load_expected_block_contract(expected_contract_path, expected_contract_sha256)
        source_contract = load_current_source_contract(source_contract_path, source_contract_sha256)
    except (CurrentRegressionError, CurrentReconstructionError) as exc:
        return {
            "schema_version": "kmfa.project_cost.expected_block_validation.private.v1",
            "validation_status": "FAIL",
            "execution_status": "FAILED",
            "validation_errors": [getattr(exc, "code", "CONTRACT_LOAD_FAILED")],
            "production_exit_code_observed": production_exit_code,
            "production_output_dir": str(production),
            "elapsed_ms": int((time.perf_counter() - start) * 1000),
        }
    if source_contract.content_sha256 != expected.current_source_contract_sha256:
        errors.append("EXPECTED_SOURCE_CONTRACT_HASH_MISMATCH")
    if production_exit_code != expected.expected_production_exit_code:
        errors.append("PRODUCTION_EXIT_CODE_MISMATCH")
    if not verify_run_seal(production):
        errors.append("PRODUCTION_RUN_SEAL_INVALID")
    if not verify_output_index(production):
        errors.append("PRODUCTION_OUTPUT_INDEX_INVALID")
    try:
        manifest = json.loads((production / "run_manifest.json").read_text(encoding="utf-8"))
        diagnostics = json.loads((production / "blocked_diagnostics.json").read_text(encoding="utf-8"))
        input_report = json.loads((production / "input_sufficiency_report.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append("PRODUCTION_DIAGNOSTICS_UNREADABLE")
        manifest, diagnostics, input_report = {}, {}, {}
    for key, expected_status in expected.expected_status_planes.items():
        if manifest.get(key) != expected_status or diagnostics.get(key) != expected_status:
            errors.append("STATUS_PLANE_MISMATCH:%s" % key)
    observed_blockers = diagnostics.get("blocker_codes")
    if observed_blockers != list(expected.expected_blocker_codes):
        errors.append("EXACT_BLOCKER_SET_MISMATCH")
    if input_report.get("overall_status") != "BLOCKED_NON_WAIVABLE" or input_report.get("user_action_required") is not True:
        errors.append("INPUT_SUFFICIENCY_STATUS_MISMATCH")
    unresolved = sorted(
        item.get("requirement_id")
        for item in input_report.get("items", [])
        if isinstance(item, dict) and item.get("observed_status") not in {"PRESENT", "NOT_IN_SCOPE"}
    )
    if unresolved != list(expected.expected_blocker_codes):
        errors.append("INPUT_REPORT_BLOCKER_SET_MISMATCH")
    isolation_items = [
        item
        for item in input_report.get("items", [])
        if isinstance(item, dict) and item.get("requirement_id") == "CALCULATE_DATA_FLOW_ISOLATION"
    ]
    if len(isolation_items) != 1 or isolation_items[0].get("observed_status") != "NOT_IN_SCOPE":
        errors.append("CALCULATE_DATA_FLOW_ISOLATION_MISSING")
    source_bindings = manifest.get("source_bindings")
    allowed_source_ids = {item.source_id for item in source_contract.selected_sources}
    if not isinstance(source_bindings, list):
        errors.append("SOURCE_BINDINGS_INVALID")
        source_bindings = []
    bound_ids = set()
    for item in source_bindings:
        if not isinstance(item, dict):
            errors.append("SOURCE_BINDING_INVALID")
            continue
        if item.get("source_slot_id") in PROHIBITED_CALCULATE_SLOT_IDS:
            errors.append("PROHIBITED_SOURCE_BINDING_PRESENT")
        source_id = item.get("opaque_source_id")
        if source_id not in allowed_source_ids:
            errors.append("UNBOUND_SOURCE_PRESENT")
        bound_ids.add(source_id)
    if bound_ids != allowed_source_ids:
        errors.append("SELECTED_SOURCE_BINDING_SET_MISMATCH")
    if any(production.glob("*.xlsx")) or (production / "INTERNAL_PROCESS_HANDOFF.md").exists():
        errors.append("FINAL_ARTIFACT_PRESENT_WHILE_BLOCKED")
    expected_request_hash = None
    if manifest:
        expected_request_hash = recompute_current_request_hash(
            run_id=str(manifest.get("run_id", "")),
            as_of=str(manifest.get("as_of", "")),
            input_root=Path(input_root),
            output_dir=production,
            contract_sha256=source_contract.content_sha256,
            observed_metadata_fingerprint=source_contract.metadata_fingerprint,
        )
        if manifest.get("request_hash") != expected_request_hash:
            errors.append("PRODUCTION_REQUEST_BINDING_MISMATCH")
    if source_contract.calculate_boundary != expected.calculate_source_boundary or any(source_contract.calculate_boundary.values()):
        errors.append("CALCULATE_SOURCE_BOUNDARY_RELAXED")
    passed = not errors
    return {
        "schema_version": "kmfa.project_cost.expected_block_validation.private.v1",
        "validation_status": "PASS" if passed else "FAIL",
        "execution_status": "EXPECTED_BLOCKED" if passed else "FAILED",
        "input_readiness_status": "BLOCKED_NON_WAIVABLE" if passed else manifest.get("input_readiness_status"),
        "calculation_status": "BLOCKED_SOURCE" if passed else manifest.get("calculation_status"),
        "generation_status": "BLOCKED_DIAGNOSTICS_GENERATED" if passed else manifest.get("generation_status"),
        "production_exit_code_observed": production_exit_code,
        "production_exit_code_expected": expected.expected_production_exit_code,
        "exact_blocker_set_match": observed_blockers == list(expected.expected_blocker_codes),
        "expected_blocker_codes": list(expected.expected_blocker_codes),
        "observed_blocker_codes": observed_blockers if isinstance(observed_blockers, list) else [],
        "project_count": expected.expected_project_count,
        "current_source_contract_sha256": source_contract.content_sha256,
        "expected_block_contract_sha256": expected.content_sha256,
        "production_request_hash_recomputed": expected_request_hash,
        "calculate_reference_data_flow_detected": False if passed else None,
        "final_financial_workbook_generated": any(production.glob("*.xlsx")),
        "internal_process_handoff_generated": (production / "INTERNAL_PROCESS_HANDOFF.md").exists(),
        "production_output_dir": str(production),
        "production_output_index": str(production / "OUTPUT_INDEX.md"),
        "validation_errors": sorted(set(errors)),
        "elapsed_ms": int((time.perf_counter() - start) * 1000),
    }


def publish_expected_block_validation(payload: Mapping[str, Any], *, output_dir: Path) -> PublishedExpectedBlockValidation:
    final_root = Path(output_dir)
    if not final_root.is_absolute() or final_root.exists() or not final_root.parent.is_dir():
        raise CurrentRegressionError("HARNESS_OUTPUT_INVALID", "harness output must be a new absolute path")
    passed = payload.get("validation_status") == "PASS" and payload.get("execution_status") == "EXPECTED_BLOCKED"
    result_status = "EXPECTED_BLOCKED" if passed else "FAILED"
    next_step = (
        "R11 精确阻断验收已通过；保持 NO_GO_PRODUCTION，进入下一 Run 前先复核本目录证据。"
        if passed
        else "查看 validation_errors，修复真实漂移；不得修改预期私有值或隐藏 blocker。"
    )
    try:
        with atomic_output_directory(final_root.parent, final_root.name) as temporary:
            _write_exclusive(temporary / "expected_block_validation.json", _json_bytes(dict(payload)))
            locator = "\n".join(
                (
                    "# Production output locator",
                    "",
                    "PRODUCTION_OUTPUT_DIR: `%s`" % payload.get("production_output_dir", ""),
                    "",
                    "PRODUCTION_OUTPUT_INDEX: `%s`" % payload.get("production_output_index", ""),
                    "",
                    "R11 仅验证预期阻断；未生成正式财务工作簿，也未进入公司内部审批流程。",
                    "",
                )
            )
            _write_exclusive(temporary / "production_output_locator.md", locator.encode("utf-8"))
            _output_controls(
                temporary,
                final_root,
                result_status=result_status,
                primary_name="expected_block_validation.json",
                next_step=next_step,
            )
            if not verify_regression_bundle(temporary):
                raise CurrentRegressionError("HARNESS_SEAL_VERIFY", "harness seal failed before publish")
    except PathSafetyError as exc:
        raise CurrentRegressionError(exc.code, exc.message) from exc
    if not verify_regression_bundle(final_root):
        raise CurrentRegressionError("HARNESS_PUBLISH_VERIFY", "published harness bundle failed seal verification")
    return PublishedExpectedBlockValidation(
        output_dir=final_root,
        primary_output=final_root / "expected_block_validation.json",
        output_index_md=final_root / "OUTPUT_INDEX.md",
        run_seal=final_root / "run_seal.sha256",
        passed=passed,
    )
