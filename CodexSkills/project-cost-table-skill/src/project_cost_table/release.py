"""R12 performance, release and aggregate-only evidence contracts.

The benchmark path verifies a sealed private snapshot but emits only counts,
timings and resource measurements. It never emits private locators, source
names, source digests or business values, and it never converts a truthful
``BLOCKED_SOURCE`` calculation into a release success.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import resource
import stat
import sys
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple

from .config_io import GovernedConfigError, load_governed_yaml_mapping
from .current_reconstruction import (
    CurrentReconstructionError,
    load_current_source_contract,
    metadata_fingerprint,
)
from .inventory import InventoryError, scan_inventory_metadata, verify_source_file
from .paths import PathSafetyError, atomic_output_directory


PERFORMANCE_SCHEMA_VERSION = "kmfa.project_cost.performance_summary.v1"
PERFORMANCE_PROFILE_ID = "KMFA-R12-RELEASE-PERFORMANCE-V1"
PERFORMANCE_BUDGET_BYTES_MAX = 256 * 1024
MAX_ALLOWED_REGRESSION_FACTOR = Decimal("1.50")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CONTROL_FILES = frozenset({"OUTPUT_INDEX.md", "output_index.json", "run_seal.sha256"})


class ReleaseError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


def _exact_keys(value: Any, expected: set[str], code: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise ReleaseError(code, "release configuration fields drifted")
    return value


def _positive_int(value: Any, code: str) -> int:
    if type(value) is not int or value <= 0:
        raise ReleaseError(code, "value must be a positive integer")
    return value


def _nonnegative_int(value: Any, code: str) -> int:
    if type(value) is not int or value < 0:
        raise ReleaseError(code, "value must be a nonnegative integer")
    return value


def _required_bool(value: Any, expected: bool, code: str) -> bool:
    if value is not expected:
        raise ReleaseError(code, "release boolean cannot be relaxed")
    return expected


def _factor(value: Any, code: str) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+\.[0-9]{2}", value):
        raise ReleaseError(code, "regression factor must be a two-decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ReleaseError(code, "regression factor is invalid") from exc
    if parsed <= 0 or parsed > MAX_ALLOWED_REGRESSION_FACTOR:
        raise ReleaseError(code, "regression factor exceeds the release ceiling")
    return parsed


@dataclass(frozen=True)
class PerformanceBudget:
    profile_id: str
    cold_process_runs: int
    subsequent_process_runs: int
    max_wall_regression_factor: Decimal
    max_peak_rss_regression_factor: Decimal
    selected_full_digest_verifications_per_source_max: int
    candidate_pair_budget_max: int
    global_unpartitioned_matching_allowed: bool
    application_cache_allowed: bool
    full_digest_required: bool
    release_gates: Mapping[str, bool]
    content_sha256: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any], *, content_sha256: str = "0" * 64) -> "PerformanceBudget":
        root = _exact_keys(
            raw,
            {"schema_version", "profile_id", "baseline", "workload", "release_gates"},
            "PERFORMANCE_BUDGET_SCHEMA",
        )
        if root["schema_version"] != "kmfa.project_cost.performance_budget.v1":
            raise ReleaseError("PERFORMANCE_BUDGET_VERSION", "unsupported performance budget schema")
        if root["profile_id"] != PERFORMANCE_PROFILE_ID:
            raise ReleaseError("PERFORMANCE_PROFILE_ID", "performance profile ID drifted")
        baseline = _exact_keys(
            root["baseline"],
            {
                "cold_process_runs",
                "subsequent_process_runs",
                "max_wall_regression_factor",
                "max_peak_rss_regression_factor",
            },
            "PERFORMANCE_BASELINE_SCHEMA",
        )
        workload = _exact_keys(
            root["workload"],
            {
                "selected_full_digest_verifications_per_source_max",
                "candidate_pair_budget_max",
                "global_unpartitioned_matching_allowed",
                "application_cache_allowed",
                "full_digest_required",
            },
            "PERFORMANCE_WORKLOAD_SCHEMA",
        )
        gates = _exact_keys(
            root["release_gates"],
            {
                "full_test_suite_required",
                "adversarial_property_metamorphic_required",
                "private_r10_r11_regression_required",
                "actual_workbook_runtime_required",
                "staged_privacy_scan_required",
                "full_digest_for_final_generation_required",
                "global_install_in_r12_allowed",
            },
            "RELEASE_GATE_SCHEMA",
        )
        cold_runs = _positive_int(baseline["cold_process_runs"], "COLD_RUN_COUNT")
        subsequent_runs = _positive_int(baseline["subsequent_process_runs"], "SUBSEQUENT_RUN_COUNT")
        if cold_runs != 1 or subsequent_runs < 3:
            raise ReleaseError("PERFORMANCE_SAMPLE_COUNTS", "release needs one cold process and at least three subsequent processes")
        digest_max = _positive_int(
            workload["selected_full_digest_verifications_per_source_max"],
            "DIGEST_VERIFICATION_MAX",
        )
        if digest_max != 1:
            raise ReleaseError("DIGEST_VERIFICATION_MAX", "each selected source may be fully verified at most once per run")
        candidate_budget = _positive_int(workload["candidate_pair_budget_max"], "CANDIDATE_PAIR_BUDGET")
        if candidate_budget > 1_000_000:
            raise ReleaseError("CANDIDATE_PAIR_BUDGET", "candidate-pair budget exceeds the governed ceiling")
        normalized_gates = {
            "full_test_suite_required": _required_bool(gates["full_test_suite_required"], True, "FULL_TEST_GATE"),
            "adversarial_property_metamorphic_required": _required_bool(gates["adversarial_property_metamorphic_required"], True, "ADVERSARIAL_GATE"),
            "private_r10_r11_regression_required": _required_bool(gates["private_r10_r11_regression_required"], True, "PRIVATE_REGRESSION_GATE"),
            "actual_workbook_runtime_required": _required_bool(gates["actual_workbook_runtime_required"], True, "WORKBOOK_RUNTIME_GATE"),
            "staged_privacy_scan_required": _required_bool(gates["staged_privacy_scan_required"], True, "STAGED_PRIVACY_GATE"),
            "full_digest_for_final_generation_required": _required_bool(gates["full_digest_for_final_generation_required"], True, "FINAL_DIGEST_GATE"),
            "global_install_in_r12_allowed": _required_bool(gates["global_install_in_r12_allowed"], False, "GLOBAL_INSTALL_BOUNDARY"),
        }
        if not SHA256_RE.fullmatch(content_sha256):
            raise ReleaseError("PERFORMANCE_BUDGET_HASH", "performance budget hash is invalid")
        return cls(
            profile_id=PERFORMANCE_PROFILE_ID,
            cold_process_runs=cold_runs,
            subsequent_process_runs=subsequent_runs,
            max_wall_regression_factor=_factor(baseline["max_wall_regression_factor"], "WALL_REGRESSION_FACTOR"),
            max_peak_rss_regression_factor=_factor(baseline["max_peak_rss_regression_factor"], "RSS_REGRESSION_FACTOR"),
            selected_full_digest_verifications_per_source_max=digest_max,
            candidate_pair_budget_max=candidate_budget,
            global_unpartitioned_matching_allowed=_required_bool(workload["global_unpartitioned_matching_allowed"], False, "GLOBAL_MATCHING_POLICY"),
            application_cache_allowed=_required_bool(workload["application_cache_allowed"], False, "APPLICATION_CACHE_POLICY"),
            full_digest_required=_required_bool(workload["full_digest_required"], True, "FULL_DIGEST_POLICY"),
            release_gates=normalized_gates,
            content_sha256=content_sha256,
        )

    @classmethod
    def from_yaml(cls, path: Path) -> "PerformanceBudget":
        try:
            raw, digest = load_governed_yaml_mapping(Path(path), max_bytes=PERFORMANCE_BUDGET_BYTES_MAX)
        except GovernedConfigError as exc:
            raise ReleaseError(exc.code, exc.message) from exc
        return cls.from_mapping(raw, content_sha256=digest)

    def public_dict(self) -> Dict[str, Any]:
        return {
            "cold_process_runs": self.cold_process_runs,
            "subsequent_process_runs": self.subsequent_process_runs,
            "max_wall_regression_factor": format(self.max_wall_regression_factor, ".2f"),
            "max_peak_rss_regression_factor": format(self.max_peak_rss_regression_factor, ".2f"),
            "selected_full_digest_verifications_per_source_max": self.selected_full_digest_verifications_per_source_max,
            "candidate_pair_budget_max": self.candidate_pair_budget_max,
            "global_unpartitioned_matching_allowed": self.global_unpartitioned_matching_allowed,
            "application_cache_allowed": self.application_cache_allowed,
            "full_digest_required": self.full_digest_required,
        }


@dataclass(frozen=True)
class PerformanceSample:
    phase: str
    sample_index: int
    wall_time_ns: int
    cpu_time_ns: int
    peak_rss_bytes: int
    bytes_read: int
    inventory_entry_count: int
    selected_source_count: int
    full_digest_verification_count: int
    max_full_digest_verifications_per_source: int
    archive_members_parsed: int
    business_files_parsed: int
    rows_parsed: int
    candidate_pairs: int
    application_cache_hits: int
    full_digest_required: bool
    full_digest_completed: bool
    global_unpartitioned_matching: bool

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "PerformanceSample":
        fields = {
            "phase",
            "sample_index",
            "wall_time_ns",
            "cpu_time_ns",
            "peak_rss_bytes",
            "bytes_read",
            "inventory_entry_count",
            "selected_source_count",
            "full_digest_verification_count",
            "max_full_digest_verifications_per_source",
            "archive_members_parsed",
            "business_files_parsed",
            "rows_parsed",
            "candidate_pairs",
            "application_cache_hits",
            "full_digest_required",
            "full_digest_completed",
            "global_unpartitioned_matching",
        }
        value = _exact_keys(raw, fields, "PERFORMANCE_SAMPLE_SCHEMA")
        if value["phase"] not in {"COLD_PROCESS", "SUBSEQUENT_PROCESS"}:
            raise ReleaseError("PERFORMANCE_SAMPLE_PHASE", "sample phase is unsupported")
        positive = {
            key: _positive_int(value[key], "PERFORMANCE_SAMPLE_VALUE")
            for key in (
                "sample_index",
                "wall_time_ns",
                "cpu_time_ns",
                "peak_rss_bytes",
                "bytes_read",
                "inventory_entry_count",
                "selected_source_count",
                "full_digest_verification_count",
                "max_full_digest_verifications_per_source",
            )
        }
        nonnegative = {
            key: _nonnegative_int(value[key], "PERFORMANCE_SAMPLE_VALUE")
            for key in (
                "archive_members_parsed",
                "business_files_parsed",
                "rows_parsed",
                "candidate_pairs",
                "application_cache_hits",
            )
        }
        for key in ("full_digest_required", "full_digest_completed", "global_unpartitioned_matching"):
            if type(value[key]) is not bool:
                raise ReleaseError("PERFORMANCE_SAMPLE_BOOLEAN", "sample booleans must not be coerced")
        return cls(
            phase=value["phase"],
            **positive,
            **nonnegative,
            full_digest_required=value["full_digest_required"],
            full_digest_completed=value["full_digest_completed"],
            global_unpartitioned_matching=value["global_unpartitioned_matching"],
        )

    def as_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


def _ratio_exceeded(actual: int, baseline: int, factor: Decimal) -> bool:
    return Decimal(actual) > Decimal(baseline) * factor


def public_hardware_profile() -> Dict[str, Any]:
    return {
        "operating_system": platform.system() or "UNKNOWN",
        "machine_architecture": platform.machine() or "UNKNOWN",
        "logical_cpu_count": os.cpu_count() or 1,
        "python_implementation": platform.python_implementation() or "UNKNOWN",
        "python_version": platform.python_version(),
    }


def release_code_fingerprint(module_root: Path) -> str:
    """Bind performance evidence to the exact release workload implementation."""

    root = Path(module_root)
    relative_paths = (
        "VERSION",
        "config/performance_budgets.yml",
        "scripts/run_release_benchmark.py",
        "src/project_cost_table/config_io.py",
        "src/project_cost_table/current_reconstruction.py",
        "src/project_cost_table/inventory.py",
        "src/project_cost_table/paths.py",
        "src/project_cost_table/release.py",
    )
    digest = hashlib.sha256()
    for relative in relative_paths:
        path = root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as exc:
            raise ReleaseError("RELEASE_CODE_UNAVAILABLE", "release fingerprint input cannot be read") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ReleaseError("RELEASE_CODE_UNSAFE", "release fingerprint input must be a single-link regular file")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return digest.hexdigest()


def _peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def measure_bound_snapshot_once(
    *,
    phase: str,
    sample_index: int,
    input_root: Path,
    contract_path: Path,
    contract_sha256: str,
) -> PerformanceSample:
    """Measure one independent-process, full-digest verification of a bound snapshot."""

    if phase not in {"COLD_PROCESS", "SUBSEQUENT_PROCESS"}:
        raise ReleaseError("PERFORMANCE_SAMPLE_PHASE", "sample phase is unsupported")
    _positive_int(sample_index, "PERFORMANCE_SAMPLE_INDEX")
    if not SHA256_RE.fullmatch(contract_sha256):
        raise ReleaseError("CONTRACT_HASH_INVALID", "contract SHA256 must be lowercase hex")
    root = Path(input_root)
    if root.is_symlink() or not root.is_dir():
        raise ReleaseError("INPUT_ROOT_INVALID", "benchmark input root must be an existing non-symlink directory")
    started_wall = time.perf_counter_ns()
    started_cpu = time.process_time_ns()
    try:
        contract = load_current_source_contract(Path(contract_path), contract_sha256)
        resolved_root = root.resolve(strict=True)
        if Path(contract.input_root).resolve(strict=True) != resolved_root:
            raise ReleaseError("CONTRACT_INPUT_ROOT_CONFLICT", "benchmark input root differs from the sealed contract")
        inventory = scan_inventory_metadata(resolved_root)
        observed_size = sum(item.identity.size_bytes for item in inventory)
        observed_unsafe = sum(item.status == "UNSAFE" for item in inventory)
        if (
            metadata_fingerprint(inventory) != contract.metadata_fingerprint
            or len(inventory) != contract.entry_count
            or observed_size != contract.total_size_bytes
            or observed_unsafe != contract.unsafe_entry_count
        ):
            raise ReleaseError("CURRENT_SOURCE_METADATA_DRIFT", "bound snapshot metadata changed before benchmark")
        entry_map = {item.source_id: item for item in inventory}
        verification_counts: Dict[str, int] = {}
        bytes_read = 0
        for locked in contract.selected_sources:
            entry = entry_map.get(locked.source_id)
            if entry is None or entry.relative_path != locked.private_relative_path:
                raise ReleaseError("CURRENT_SELECTED_SOURCE_DRIFT", "a selected source no longer matches its sealed locator")
            verified = verify_source_file(resolved_root, entry)
            if verified.sha256 != locked.sha256:
                raise ReleaseError("CURRENT_SELECTED_SOURCE_HASH_DRIFT", "a selected source differs from its full digest lock")
            verification_counts[locked.source_id] = verification_counts.get(locked.source_id, 0) + 1
            bytes_read += verified.identity.size_bytes
    except (CurrentReconstructionError, InventoryError, OSError) as exc:
        code = getattr(exc, "code", "BOUND_SNAPSHOT_UNAVAILABLE")
        message = getattr(exc, "message", "bound snapshot cannot be verified")
        raise ReleaseError(code, message) from exc
    wall = time.perf_counter_ns() - started_wall
    cpu = time.process_time_ns() - started_cpu
    return PerformanceSample(
        phase=phase,
        sample_index=sample_index,
        wall_time_ns=max(wall, 1),
        cpu_time_ns=max(cpu, 1),
        peak_rss_bytes=max(_peak_rss_bytes(), 1),
        bytes_read=bytes_read,
        inventory_entry_count=len(inventory),
        selected_source_count=len(contract.selected_sources),
        full_digest_verification_count=sum(verification_counts.values()),
        max_full_digest_verifications_per_source=max(verification_counts.values()),
        archive_members_parsed=0,
        business_files_parsed=0,
        rows_parsed=0,
        candidate_pairs=0,
        application_cache_hits=0,
        full_digest_required=True,
        full_digest_completed=True,
        global_unpartitioned_matching=False,
    )


def evaluate_performance(
    budget: PerformanceBudget,
    samples: Sequence[PerformanceSample],
    *,
    hardware: Mapping[str, Any] | None = None,
    product_version: str = "0.2.0",
    release_code_sha256: str = "0" * 64,
) -> Dict[str, Any]:
    if product_version != "0.2.0":
        raise ReleaseError("PERFORMANCE_PRODUCT_VERSION", "performance evidence must bind released product 0.2.0")
    if not SHA256_RE.fullmatch(release_code_sha256):
        raise ReleaseError("RELEASE_CODE_HASH", "release code fingerprint is invalid")
    normalized = tuple(PerformanceSample.from_mapping(item.as_dict()) for item in samples)
    cold = tuple(item for item in normalized if item.phase == "COLD_PROCESS")
    subsequent = tuple(item for item in normalized if item.phase == "SUBSEQUENT_PROCESS")
    issues = []
    if len(cold) != budget.cold_process_runs:
        issues.append("COLD_SAMPLE_COUNT_MISMATCH")
    if len(subsequent) != budget.subsequent_process_runs:
        issues.append("SUBSEQUENT_SAMPLE_COUNT_MISMATCH")
    indices = [(item.phase, item.sample_index) for item in normalized]
    if len(indices) != len(set(indices)):
        issues.append("SAMPLE_INDEX_DUPLICATE")
    for item in normalized:
        if not item.full_digest_required or not item.full_digest_completed:
            issues.append("FULL_DIGEST_NOT_COMPLETED")
        if item.full_digest_verification_count != item.selected_source_count:
            issues.append("DIGEST_VERIFICATION_COUNT_MISMATCH")
        if item.max_full_digest_verifications_per_source > budget.selected_full_digest_verifications_per_source_max:
            issues.append("SOURCE_PARSED_OR_HASHED_MORE_THAN_ONCE")
        if item.candidate_pairs > budget.candidate_pair_budget_max:
            issues.append("CANDIDATE_PAIR_BUDGET_EXCEEDED")
        if item.global_unpartitioned_matching or item.global_unpartitioned_matching != budget.global_unpartitioned_matching_allowed:
            issues.append("GLOBAL_UNPARTITIONED_MATCHING_FORBIDDEN")
        if item.application_cache_hits and not budget.application_cache_allowed:
            issues.append("APPLICATION_CACHE_FORBIDDEN")
    if len(cold) == 1:
        baseline = cold[0]
        for item in subsequent:
            if (
                item.bytes_read != baseline.bytes_read
                or item.inventory_entry_count != baseline.inventory_entry_count
                or item.selected_source_count != baseline.selected_source_count
                or item.full_digest_verification_count != baseline.full_digest_verification_count
                or item.archive_members_parsed != baseline.archive_members_parsed
                or item.business_files_parsed != baseline.business_files_parsed
                or item.rows_parsed != baseline.rows_parsed
                or item.candidate_pairs != baseline.candidate_pairs
            ):
                issues.append("WORKLOAD_SCOPE_DRIFT")
            if _ratio_exceeded(item.wall_time_ns, baseline.wall_time_ns, budget.max_wall_regression_factor):
                issues.append("WALL_TIME_REGRESSION")
            if _ratio_exceeded(item.peak_rss_bytes, baseline.peak_rss_bytes, budget.max_peak_rss_regression_factor):
                issues.append("PEAK_RSS_REGRESSION")
    ordered = tuple(sorted(normalized, key=lambda item: (0 if item.phase == "COLD_PROCESS" else 1, item.sample_index)))
    if cold and subsequent:
        aggregate = {
            "cold_wall_time_ns": cold[0].wall_time_ns,
            "cold_peak_rss_bytes": cold[0].peak_rss_bytes,
            "max_subsequent_wall_time_ns": max(item.wall_time_ns for item in subsequent),
            "max_subsequent_peak_rss_bytes": max(item.peak_rss_bytes for item in subsequent),
            "total_bytes_read": sum(item.bytes_read for item in ordered),
            "total_full_digest_verifications": sum(item.full_digest_verification_count for item in ordered),
            "max_full_digest_verifications_per_source": max(item.max_full_digest_verifications_per_source for item in ordered),
            "total_candidate_pairs": sum(item.candidate_pairs for item in ordered),
            "total_application_cache_hits": sum(item.application_cache_hits for item in ordered),
        }
    else:
        aggregate = {
            "cold_wall_time_ns": cold[0].wall_time_ns if cold else 1,
            "cold_peak_rss_bytes": cold[0].peak_rss_bytes if cold else 1,
            "max_subsequent_wall_time_ns": max((item.wall_time_ns for item in subsequent), default=1),
            "max_subsequent_peak_rss_bytes": max((item.peak_rss_bytes for item in subsequent), default=1),
            "total_bytes_read": max(sum(item.bytes_read for item in ordered), 1),
            "total_full_digest_verifications": max(sum(item.full_digest_verification_count for item in ordered), 1),
            "max_full_digest_verifications_per_source": max((item.max_full_digest_verifications_per_source for item in ordered), default=1),
            "total_candidate_pairs": sum(item.candidate_pairs for item in ordered),
            "total_application_cache_hits": sum(item.application_cache_hits for item in ordered),
        }
    return {
        "schema_version": PERFORMANCE_SCHEMA_VERSION,
        "profile_id": budget.profile_id,
        "product_version": product_version,
        "release_code_sha256": release_code_sha256,
        "performance_budget_sha256": budget.content_sha256,
        "release_scope": "BOUND_CURRENT_SOURCE_DIGEST_GATE",
        "status": "PASS" if not issues else "FAILED",
        "issues": sorted(set(issues)),
        "hardware": dict(hardware or public_hardware_profile()),
        "budget": budget.public_dict(),
        "samples": [item.as_dict() for item in ordered],
        "aggregate": aggregate,
        "real_calculation_baseline_status": "NOT_EVALUATED_BLOCKED_SOURCE",
        "privacy": {
            "contains_private_locators": False,
            "contains_source_names": False,
            "contains_source_hashes": False,
            "contains_business_values": False,
        },
        "company_approval_state_managed": False,
        "global_install_performed": False,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_exclusive(path: Path, data: bytes) -> None:
    with Path(path).open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


@dataclass(frozen=True)
class PublishedPerformanceSummary:
    output_dir: Path
    primary_output: Path
    output_index_md: Path
    run_seal: Path
    passed: bool

    def locator_text(self) -> str:
        return "\n".join(
            (
                "RESULT_STATUS: %s" % ("PERFORMANCE_PASS" if self.passed else "PERFORMANCE_FAILED"),
                "OUTPUT_DIR: %s" % self.output_dir,
                "PRIMARY_OUTPUT: %s" % self.primary_output,
                "OUTPUT_INDEX: %s" % self.output_index_md,
                "NEXT_STEP: %s"
                % (
                    "继续完成 R12 全测试、真实工作簿、私有回归和 staged privacy 门禁；本结果不代表当前正式计算可用。"
                    if self.passed
                    else "查看 performance_summary.json 的 issues；不得放宽预算或把真实计算 BLOCKED 改写为 PASS。"
                ),
            )
        )


def publish_performance_summary(summary: Mapping[str, Any], *, output_dir: Path) -> PublishedPerformanceSummary:
    final_root = Path(output_dir)
    if not final_root.is_absolute() or final_root.exists() or not final_root.parent.is_dir():
        raise ReleaseError("OUTPUT_DIR_INVALID", "release output must be a new absolute directory with an existing parent")
    passed = summary.get("status") == "PASS"
    try:
        with atomic_output_directory(final_root.parent, final_root.name) as staging:
            primary = staging / "performance_summary.json"
            _write_exclusive(
                primary,
                (json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            )
            digest = _sha256_file(primary)
            next_step = (
                "继续完成 R12 其余门禁；真实 calculate 仍须先补齐输入。"
                if passed
                else "修复性能或资源门禁后使用新的输出目录重跑。"
            )
            md = "\n".join(
                (
                    "# R12 performance output index",
                    "",
                    "RESULT_STATUS: `%s`" % ("PERFORMANCE_PASS" if passed else "PERFORMANCE_FAILED"),
                    "",
                    "OUTPUT_DIR: `%s`" % final_root,
                    "",
                    "PRIMARY_OUTPUT: `%s`" % (final_root / primary.name),
                    "",
                    "OUTPUT_INDEX: `%s`" % (final_root / "OUTPUT_INDEX.md"),
                    "",
                    "| Artifact | SHA256 | Absolute path |",
                    "| --- | --- | --- |",
                    "| `%s` | `%s` | `%s` |" % (primary.name, digest, final_root / primary.name),
                    "",
                    "NEXT_STEP: %s" % next_step,
                    "",
                )
            )
            _write_exclusive(staging / "OUTPUT_INDEX.md", md.encode("utf-8"))
            index = {
                "schema_version": "kmfa.project_cost.performance_output_index.private.v1",
                "result_status": "PERFORMANCE_PASS" if passed else "PERFORMANCE_FAILED",
                "output_dir": str(final_root),
                "primary_output": str(final_root / primary.name),
                "output_index": str(final_root / "OUTPUT_INDEX.md"),
                "seal_path": str(final_root / "run_seal.sha256"),
                "files": [{"path": str(final_root / primary.name), "sha256": digest, "artifact_type": primary.name}],
                "next_step": next_step,
            }
            _write_exclusive(
                staging / "output_index.json",
                (json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            )
            seal_lines = []
            for path in sorted(
                (item for item in staging.iterdir() if item.is_file() and item.name != "run_seal.sha256"),
                key=lambda item: item.name,
            ):
                seal_lines.append("%s  %s" % (_sha256_file(path), path.name))
            _write_exclusive(staging / "run_seal.sha256", ("\n".join(seal_lines) + "\n").encode("ascii"))
    except PathSafetyError as exc:
        raise ReleaseError(exc.code, exc.message) from exc
    return PublishedPerformanceSummary(
        output_dir=final_root,
        primary_output=final_root / "performance_summary.json",
        output_index_md=final_root / "OUTPUT_INDEX.md",
        run_seal=final_root / "run_seal.sha256",
        passed=passed,
    )


def verify_performance_bundle(output_dir: Path) -> bool:
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
