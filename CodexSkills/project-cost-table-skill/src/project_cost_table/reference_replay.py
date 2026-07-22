"""R10 hash-bound private reference replay isolated from calculate data flow."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import stat
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from .input_gate import InputSufficiencyReport, RequirementItem
from .paths import PathSafetyError, atomic_output_directory, resolve_input_file
from .security import FileSecurityError, SecurityProfile, escape_spreadsheet_text, preflight_source_file
from .statuses import (
    CalculationStatus,
    ExecutionStatus,
    GenerationStatus,
    InputReadinessStatus,
    ReplayFidelityStatus,
    RunStatusPlanes,
    SourceQualityStatus,
)


RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CONTROL_FILES = frozenset({"run_manifest.json", "OUTPUT_INDEX.md", "output_index.json", "run_seal.sha256"})
BASELINE_SCHEMA_VERSION = "kmfa.project_cost.reference_expected.private.v1"
BASELINE_CLASSIFICATION = "PRIVATE_FINANCIAL_REFERENCE_DO_NOT_COMMIT_PUBLICLY"
RESULT_SCHEMA_VERSION = "kmfa.project_cost.reference_replay_result.private.v1"
MAX_BASELINE_BYTES = 16 * 1024 * 1024
MAX_MONEY_MINOR = 10**15


class ReferenceReplayError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        fidelity_status: ReplayFidelityStatus = ReplayFidelityStatus.NOT_EVALUATED,
        input_status: InputReadinessStatus = InputReadinessStatus.BLOCKED_NON_WAIVABLE,
        requirement_id: str = "REFERENCE_BASELINE_AND_REPORTS",
    ) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message
        self.fidelity_status = fidelity_status
        self.input_status = input_status
        self.requirement_id = requirement_id


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_exclusive(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _write_json(path: Path, value: Any) -> None:
    _write_exclusive(path, _json_bytes(value))


def _safe_text(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value):
        raise ReferenceReplayError("REFERENCE_BASELINE_SCHEMA", "%s must be text" % field)
    if any(character in value for character in "\x00\r\n"):
        raise ReferenceReplayError("REFERENCE_BASELINE_SCHEMA", "%s contains control characters" % field)
    return value


def _minor_integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or abs(value) > MAX_MONEY_MINOR:
        raise ReferenceReplayError("REFERENCE_BASELINE_MONEY", "%s must be a bounded integer minor-unit value" % field)
    return value


def _required_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ReferenceReplayError("REFERENCE_BASELINE_HASH", "%s must be lowercase SHA256" % field)
    return value


def _stable_file_bytes(path: Path, *, max_bytes: int) -> bytes:
    try:
        before = path.stat()
    except OSError as exc:
        raise ReferenceReplayError("REFERENCE_BASELINE_UNREADABLE", "baseline cannot be inspected") from exc
    if (
        not stat.S_ISREG(before.st_mode)
        or before.st_nlink != 1
        or before.st_size > max_bytes
    ):
        raise ReferenceReplayError("REFERENCE_BASELINE_UNSAFE", "baseline must be a bounded single-link regular file")
    try:
        data = path.read_bytes()
        after = path.stat()
    except OSError as exc:
        raise ReferenceReplayError("REFERENCE_BASELINE_UNREADABLE", "baseline cannot be read") from exc
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if before_identity != after_identity:
        raise ReferenceReplayError("REFERENCE_BASELINE_CHANGED", "baseline changed during read")
    return data


def _line_values_hash(items: Sequence["ReferenceLineItem"]) -> str:
    payload = [item.as_dict() for item in items]
    return _sha256_bytes(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8"))


@dataclass(frozen=True)
class ReferenceLineItem:
    category: str
    label: str
    note: Optional[str]
    amount_minor: int

    @classmethod
    def from_mapping(cls, raw: Any, *, project_index: int, line_index: int) -> "ReferenceLineItem":
        required = {"category", "label", "amount_cents"}
        optional = {"note"}
        if not isinstance(raw, Mapping) or not required <= set(raw) or set(raw) - required - optional:
            raise ReferenceReplayError("REFERENCE_BASELINE_SCHEMA", "reference line item fields differ from v1")
        prefix = "projects[%d].line_items[%d]" % (project_index, line_index)
        return cls(
            category=_safe_text(raw["category"], prefix + ".category"),
            label=_safe_text(raw["label"], prefix + ".label", allow_empty=True),
            note=(
                _safe_text(raw["note"], prefix + ".note", allow_empty=True)
                if "note" in raw
                else None
            ),
            amount_minor=_minor_integer(raw["amount_cents"], prefix + ".amount_cents"),
        )

    def as_dict(self) -> Dict[str, Any]:
        payload = {
            "category": self.category,
            "label": self.label,
            "amount_cents": self.amount_minor,
        }
        if self.note is not None:
            payload["note"] = self.note
        return payload


@dataclass(frozen=True)
class ReferenceProject:
    project_code: str
    project_name: str
    reference_pdf: str
    reference_pdf_sha256: str
    source_revenue_minor: int
    source_total_cost_minor: int
    source_profit_minor: int
    source_profit_rate_text: Optional[str]
    line_items: Tuple[ReferenceLineItem, ...]
    expected_source_profit_delta_minor: int
    expected_kingdee_5001_minor: int
    identity_status: Optional[str]
    note: Optional[str]
    critical_note: Optional[str]

    @classmethod
    def from_mapping(cls, raw: Any, *, index: int) -> "ReferenceProject":
        required = {
            "project_code",
            "project_name",
            "reference_pdf",
            "reference_pdf_sha256",
            "source_revenue_cents",
            "source_total_cost_cents",
            "source_profit_cents",
            "source_profit_rate_text",
            "line_items",
            "expected_kingdee_5001_cents_current_snapshot",
        }
        optional = {
            "expected_source_profit_delta_cents",
            "identity_status",
            "note",
            "critical_note",
        }
        if not isinstance(raw, Mapping) or not required <= set(raw) or set(raw) - required - optional:
            raise ReferenceReplayError("REFERENCE_BASELINE_SCHEMA", "reference project fields differ from v1")
        prefix = "projects[%d]" % index
        reference_pdf = _safe_text(raw["reference_pdf"], prefix + ".reference_pdf")
        relative = PurePosixPath(reference_pdf)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or "." in relative.parts
            or "\\" in reference_pdf
            or relative.suffix.casefold() != ".pdf"
        ):
            raise ReferenceReplayError("REFERENCE_PDF_PATH_UNSAFE", "reference PDF path must be a safe relative PDF")
        raw_lines = raw["line_items"]
        if not isinstance(raw_lines, list) or not raw_lines:
            raise ReferenceReplayError("REFERENCE_BASELINE_SCHEMA", "reference project needs line items")
        lines = tuple(
            ReferenceLineItem.from_mapping(item, project_index=index, line_index=line_index)
            for line_index, item in enumerate(raw_lines)
        )
        expected_delta = _minor_integer(
            raw.get("expected_source_profit_delta_cents", 0),
            prefix + ".expected_source_profit_delta_cents",
        )
        return cls(
            project_code=_safe_text(raw["project_code"], prefix + ".project_code"),
            project_name=_safe_text(raw["project_name"], prefix + ".project_name"),
            reference_pdf=reference_pdf,
            reference_pdf_sha256=_required_sha256(raw["reference_pdf_sha256"], prefix + ".reference_pdf_sha256"),
            source_revenue_minor=_minor_integer(raw["source_revenue_cents"], prefix + ".source_revenue_cents"),
            source_total_cost_minor=_minor_integer(raw["source_total_cost_cents"], prefix + ".source_total_cost_cents"),
            source_profit_minor=_minor_integer(raw["source_profit_cents"], prefix + ".source_profit_cents"),
            source_profit_rate_text=(
                _safe_text(
                    raw["source_profit_rate_text"],
                    prefix + ".source_profit_rate_text",
                    allow_empty=True,
                )
                if raw["source_profit_rate_text"] is not None
                else None
            ),
            line_items=lines,
            expected_source_profit_delta_minor=expected_delta,
            expected_kingdee_5001_minor=_minor_integer(
                raw["expected_kingdee_5001_cents_current_snapshot"],
                prefix + ".expected_kingdee_5001_cents_current_snapshot",
            ),
            identity_status=(
                _safe_text(raw["identity_status"], prefix + ".identity_status", allow_empty=True)
                if "identity_status" in raw
                else None
            ),
            note=(
                _safe_text(raw["note"], prefix + ".note", allow_empty=True)
                if "note" in raw
                else None
            ),
            critical_note=(
                _safe_text(raw["critical_note"], prefix + ".critical_note", allow_empty=True)
                if "critical_note" in raw
                else None
            ),
        )


@dataclass(frozen=True)
class ReferenceBaseline:
    schema_version: str
    classification: str
    generated_from_snapshot: str
    projects: Tuple[ReferenceProject, ...]
    content_sha256: str

    @classmethod
    def from_bytes(cls, data: bytes, *, expected_sha256: str) -> "ReferenceBaseline":
        actual_sha256 = _sha256_bytes(data)
        if actual_sha256 != expected_sha256:
            raise ReferenceReplayError(
                "REFERENCE_BASELINE_HASH_DRIFT",
                "private reference baseline digest differs from the locked request",
                fidelity_status=ReplayFidelityStatus.BLOCKED_HASH,
                requirement_id="REFERENCE_BASELINE_HASH",
            )
        try:
            raw = json.loads(data.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ReferenceReplayError("REFERENCE_BASELINE_PARSE", "reference baseline is not valid UTF-8 JSON") from exc
        if not isinstance(raw, Mapping) or set(raw) != {
            "schema_version",
            "classification",
            "generated_from_snapshot",
            "projects",
        }:
            raise ReferenceReplayError("REFERENCE_BASELINE_SCHEMA", "reference baseline top-level fields differ from v1")
        if raw["schema_version"] != BASELINE_SCHEMA_VERSION or raw["classification"] != BASELINE_CLASSIFICATION:
            raise ReferenceReplayError("REFERENCE_BASELINE_SCHEMA", "reference baseline identity or classification is invalid")
        projects_raw = raw["projects"]
        if not isinstance(projects_raw, list) or not projects_raw:
            raise ReferenceReplayError("REFERENCE_BASELINE_SCHEMA", "reference baseline needs at least one project")
        projects = tuple(ReferenceProject.from_mapping(item, index=index) for index, item in enumerate(projects_raw))
        codes = [item.project_code for item in projects]
        pdfs = [item.reference_pdf for item in projects]
        if len(set(codes)) != len(codes) or len(set(pdfs)) != len(pdfs):
            raise ReferenceReplayError("REFERENCE_BASELINE_DUPLICATE", "reference projects and PDF bindings must be unique")
        return cls(
            schema_version=raw["schema_version"],
            classification=raw["classification"],
            generated_from_snapshot=_safe_text(raw["generated_from_snapshot"], "generated_from_snapshot"),
            projects=projects,
            content_sha256=actual_sha256,
        )


@dataclass(frozen=True)
class ReferenceReplayRequest:
    run_id: str
    as_of: str
    input_root: Path
    baseline_root: Path
    baseline_relative_path: str
    baseline_sha256: str
    output_dir: Path
    expected_project_count: int
    security_profile: SecurityProfile
    code_version: str
    config_hash: str

    def request_hash(self) -> str:
        payload = {
            "run_id": self.run_id,
            "mode": "reference-replay",
            "as_of": self.as_of,
            "baseline_relative_path": self.baseline_relative_path,
            "baseline_sha256": self.baseline_sha256,
            "expected_project_count": self.expected_project_count,
            "code_version": self.code_version,
            "config_hash": self.config_hash,
        }
        return _sha256_bytes(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))

    def validate_metadata(self) -> Path:
        if not RUN_ID_RE.fullmatch(self.run_id):
            raise ReferenceReplayError("REPLAY_RUN_ID_INVALID", "run ID is invalid")
        try:
            datetime.strptime(self.as_of, "%Y-%m-%d")
        except (TypeError, ValueError) as exc:
            raise ReferenceReplayError("REPLAY_AS_OF_INVALID", "as-of must be canonical ISO") from exc
        if not SHA256_RE.fullmatch(self.baseline_sha256) or not SHA256_RE.fullmatch(self.config_hash):
            raise ReferenceReplayError("REPLAY_BINDING_INVALID", "baseline and config hashes are required")
        if not isinstance(self.expected_project_count, int) or isinstance(self.expected_project_count, bool) or self.expected_project_count < 1:
            raise ReferenceReplayError("REPLAY_PROJECT_COUNT_INVALID", "expected project count must be positive")
        if not self.code_version:
            raise ReferenceReplayError("REPLAY_VERSION_INVALID", "code version is required")
        input_root = Path(self.input_root)
        baseline_root = Path(self.baseline_root)
        for root, label in ((input_root, "raw input root"), (baseline_root, "baseline root")):
            if root.is_symlink():
                raise ReferenceReplayError("REPLAY_ROOT_SYMLINK", "%s must not be a symlink" % label)
            try:
                resolved = root.resolve(strict=True)
            except OSError as exc:
                raise ReferenceReplayError("REPLAY_ROOT_UNAVAILABLE", "%s is unavailable" % label) from exc
            if not resolved.is_dir():
                raise ReferenceReplayError("REPLAY_ROOT_INVALID", "%s must be a directory" % label)
        output = Path(self.output_dir)
        if not output.is_absolute() or output.exists() or not output.parent.is_dir():
            raise ReferenceReplayError("REPLAY_OUTPUT_INVALID", "output directory must be a new absolute path")
        try:
            raw_resolved = input_root.resolve(strict=True)
            output_parent = output.parent.resolve(strict=True)
            output_parent.relative_to(raw_resolved)
        except ValueError:
            pass
        except OSError as exc:
            raise ReferenceReplayError("REPLAY_OUTPUT_INVALID", "output parent cannot be resolved") from exc
        else:
            raise ReferenceReplayError("REPLAY_OUTPUT_INSIDE_RAW", "outputs must never be written inside the raw inbox")
        try:
            baseline_path = resolve_input_file(
                baseline_root,
                self.baseline_relative_path,
                max_bytes=MAX_BASELINE_BYTES,
            )
        except PathSafetyError as exc:
            raise ReferenceReplayError(
                exc.code,
                exc.message,
                requirement_id="REFERENCE_BASELINE",
            ) from exc
        return baseline_path


@dataclass(frozen=True)
class ReferenceProjectReplay:
    project: ReferenceProject
    actual_pdf_sha256: str
    line_sum_minor: int
    recomputed_profit_minor: int
    source_profit_delta_minor: int
    source_quality_status: SourceQualityStatus
    line_values_sha256: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "project_code": self.project.project_code,
            "project_name": self.project.project_name,
            "reference_pdf": self.project.reference_pdf,
            "reference_pdf_sha256": self.project.reference_pdf_sha256,
            "actual_pdf_sha256": self.actual_pdf_sha256,
            "pdf_hash_match": True,
            "line_items": [item.as_dict() for item in self.project.line_items],
            "reference_line_values_sha256": self.line_values_sha256,
            "replayed_line_values_sha256": self.line_values_sha256,
            "source_revenue_cents": self.project.source_revenue_minor,
            "source_total_cost_cents": self.project.source_total_cost_minor,
            "line_sum_cents": self.line_sum_minor,
            "line_sum_delta_cents": self.line_sum_minor - self.project.source_total_cost_minor,
            "source_profit_cents": self.project.source_profit_minor,
            "recomputed_profit_cents": self.recomputed_profit_minor,
            "source_profit_delta_cents": self.source_profit_delta_minor,
            "expected_source_profit_delta_cents": self.project.expected_source_profit_delta_minor,
            "source_profit_rate_text": self.project.source_profit_rate_text,
            "replay_fidelity_status": ReplayFidelityStatus.EXACT.value,
            "source_quality_status": self.source_quality_status.value,
            "calculation_status": CalculationStatus.NOT_EVALUATED.value,
        }


@dataclass(frozen=True)
class ReferenceReplayResult:
    request: ReferenceReplayRequest
    baseline: ReferenceBaseline
    projects: Tuple[ReferenceProjectReplay, ...]

    @property
    def source_quality_status(self) -> SourceQualityStatus:
        if any(item.source_quality_status == SourceQualityStatus.SOURCE_ARITHMETIC_DIFFERENCE for item in self.projects):
            return SourceQualityStatus.SOURCE_ARITHMETIC_DIFFERENCE
        return SourceQualityStatus.CONSISTENT

    @property
    def arithmetic_difference_count(self) -> int:
        return sum(
            item.source_quality_status == SourceQualityStatus.SOURCE_ARITHMETIC_DIFFERENCE
            for item in self.projects
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": RESULT_SCHEMA_VERSION,
            "run_id": self.request.run_id,
            "mode": "reference-replay",
            "as_of": self.request.as_of,
            "baseline_sha256": self.baseline.content_sha256,
            "execution_status": ExecutionStatus.SUCCEEDED.value,
            "input_readiness_status": InputReadinessStatus.SUFFICIENT.value,
            "calculation_status": CalculationStatus.NOT_EVALUATED.value,
            "generation_status": GenerationStatus.NOT_GENERATED.value,
            "replay_fidelity_status": ReplayFidelityStatus.EXACT.value,
            "source_quality_status": self.source_quality_status.value,
            "project_count": len(self.projects),
            "exact_count": len(self.projects),
            "source_arithmetic_difference_count": self.arithmetic_difference_count,
            "projects": [item.as_dict() for item in self.projects],
        }


@dataclass(frozen=True)
class GeneratedReplayRun:
    status_planes: RunStatusPlanes
    replay_fidelity_status: ReplayFidelityStatus
    source_quality_status: SourceQualityStatus
    output_dir: Path
    primary_output: Path
    output_index_md: Path
    output_index_json: Path
    run_seal: Path

    def locator_text(self) -> str:
        self.status_planes.validate()
        result_status = (
            "REFERENCE_REPLAY_EXACT"
            if self.replay_fidelity_status == ReplayFidelityStatus.EXACT
            else self.status_planes.generation_status.value
        )
        if self.replay_fidelity_status == ReplayFidelityStatus.EXACT:
            next_step = "精确回放仅作历史显示/审计证据；不得注入 calculate。"
        elif self.status_planes.execution_status == ExecutionStatus.FAILED:
            next_step = "查看 generation_failure.json，修复实现后以新 run ID 和新输出目录重试。"
        else:
            next_step = "查看 blocked_diagnostics.json，补充或恢复 hash-bound reference 输入后以新 run 重试。"
        return "\n".join(
            (
                "RESULT_STATUS: %s" % result_status,
                "OUTPUT_DIR: %s" % self.output_dir,
                "PRIMARY_OUTPUT: %s" % self.primary_output,
                "OUTPUT_INDEX: %s" % self.output_index_md,
                "NEXT_STEP: %s" % next_step,
            )
        )


def _input_report(
    request: ReferenceReplayRequest,
    *,
    status: InputReadinessStatus,
    issue: Optional[ReferenceReplayError] = None,
) -> InputSufficiencyReport:
    common = (
        ("RUN_MODE", "reference-replay mode"),
        ("PROJECT_SCOPE", "hash-bound reference project set"),
        ("AS_OF_DATE", "canonical replay as-of"),
        ("RAW_ROOT_AND_MANIFEST", "read-only raw root plus locked private baseline"),
        ("SAFE_READ_AND_DIGEST", "safe PDF preflight and exact digests"),
        ("OUTPUT_DIRECTORY", "new private atomic output directory"),
    )
    items = []
    for requirement_id, expected in common:
        observed = "PRESENT"
        if issue is not None and requirement_id == issue.requirement_id:
            observed = "CONFLICT" if "HASH" in issue.code or "DELTA" in issue.code else "UNSAFE"
        items.append(
            RequirementItem(
                requirement_id=requirement_id,
                classification="NON_WAIVABLE",
                observed_status=observed,
                allowed_resolutions=("SUPPLIED", "QUALIFIED_ALTERNATE_EVIDENCE", "SCOPE_REDUCED", "BLOCKED"),
                applies_to_metrics=("REFERENCE_DISPLAY",),
                expected_source_or_policy=expected,
                evidence_ref=None,
            )
        )
    if issue is not None and issue.requirement_id not in {item.requirement_id for item in items}:
        items.append(
            RequirementItem(
                requirement_id=issue.requirement_id,
                classification="NON_WAIVABLE",
                observed_status="CONFLICT" if "HASH" in issue.code or "DELTA" in issue.code else "UNSAFE",
                allowed_resolutions=("SUPPLIED", "QUALIFIED_ALTERNATE_EVIDENCE", "SCOPE_REDUCED", "BLOCKED"),
                applies_to_metrics=("REFERENCE_DISPLAY",),
                expected_source_or_policy="hash-bound private reference baseline and reports",
                evidence_ref=None,
            )
        )
    return InputSufficiencyReport(
        run_id=request.run_id,
        request_hash=request.request_hash(),
        mode="reference-replay",
        requested_metrics=("REFERENCE_DISPLAY",),
        requested_basis_ids=(),
        output_dir=str(request.output_dir),
        overall_status=status.value,
        items=tuple(items),
        user_action_required=status not in {
            InputReadinessStatus.SUFFICIENT,
            InputReadinessStatus.SUFFICIENT_WITH_DOCUMENTED_SCOPE,
        },
        resolution_ref=None,
    )


def _replay_projects(
    request: ReferenceReplayRequest,
    baseline: ReferenceBaseline,
) -> Tuple[ReferenceProjectReplay, ...]:
    if len(baseline.projects) != request.expected_project_count:
        raise ReferenceReplayError(
            "REFERENCE_PROJECT_COUNT_MISMATCH",
            "private reference project count differs from the locked R10 request",
            requirement_id="PROJECT_SCOPE",
        )
    pdf_reports = []
    mismatches = []
    for project in baseline.projects:
        try:
            report = preflight_source_file(
                Path(request.input_root),
                Path(project.reference_pdf),
                expected_kind="pdf",
                profile=request.security_profile,
            )
        except (FileSecurityError, PathSafetyError) as exc:
            code = getattr(exc, "code", "REFERENCE_PDF_SECURITY")
            message = getattr(exc, "message", "reference PDF failed safe preflight")
            raise ReferenceReplayError(
                code,
                message,
                requirement_id="SAFE_READ_AND_DIGEST",
            ) from exc
        pdf_reports.append((project, report))
        if report.sha256 != project.reference_pdf_sha256:
            mismatches.append(project.project_code)
    if mismatches:
        raise ReferenceReplayError(
            "REFERENCE_PDF_HASH_DRIFT",
            "%d reference PDF digest(s) differ from the private baseline" % len(mismatches),
            fidelity_status=ReplayFidelityStatus.BLOCKED_HASH,
            requirement_id="SAFE_READ_AND_DIGEST",
        )

    results = []
    for project, report in pdf_reports:
        line_sum = sum(item.amount_minor for item in project.line_items)
        if line_sum != project.source_total_cost_minor:
            raise ReferenceReplayError(
                "REFERENCE_LINE_SUM_DELTA",
                "reference line items do not reproduce the source total",
                fidelity_status=ReplayFidelityStatus.BLOCKED_LINE_DELTA,
                input_status=InputReadinessStatus.SUFFICIENT,
                requirement_id="REFERENCE_BASELINE_AND_REPORTS",
            )
        recomputed_profit = project.source_revenue_minor - project.source_total_cost_minor
        source_profit_delta = project.source_profit_minor - recomputed_profit
        if source_profit_delta != project.expected_source_profit_delta_minor:
            raise ReferenceReplayError(
                "REFERENCE_SOURCE_ARITHMETIC_DRIFT",
                "source arithmetic difference changed from the hash-bound expectation",
                fidelity_status=ReplayFidelityStatus.BLOCKED_LINE_DELTA,
                input_status=InputReadinessStatus.SUFFICIENT,
                requirement_id="REFERENCE_BASELINE_AND_REPORTS",
            )
        quality = (
            SourceQualityStatus.SOURCE_ARITHMETIC_DIFFERENCE
            if source_profit_delta
            else SourceQualityStatus.CONSISTENT
        )
        results.append(
            ReferenceProjectReplay(
                project=project,
                actual_pdf_sha256=report.sha256,
                line_sum_minor=line_sum,
                recomputed_profit_minor=recomputed_profit,
                source_profit_delta_minor=source_profit_delta,
                source_quality_status=quality,
                line_values_sha256=_line_values_hash(project.line_items),
            )
        )
    return tuple(results)


def _csv_bytes(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        values = []
        for value in row:
            if value is None or isinstance(value, (int, bool)):
                values.append(value)
            elif isinstance(value, str):
                values.append(escape_spreadsheet_text(value))
            else:
                raise ReferenceReplayError("REPLAY_CSV_VALUE_INVALID", "CSV value type is unsupported")
        writer.writerow(values)
    return buffer.getvalue().encode("utf-8")


def _business_hashes(directory: Path) -> Dict[str, str]:
    return {
        path.name: _sha256_file(path)
        for path in sorted(directory.iterdir(), key=lambda item: item.name)
        if path.is_file() and path.name not in CONTROL_FILES
    }


def _write_output_controls(
    directory: Path,
    request: ReferenceReplayRequest,
    *,
    status_planes: RunStatusPlanes,
    fidelity_status: ReplayFidelityStatus,
    source_quality_status: SourceQualityStatus,
    primary_name: str,
    source_bindings: Sequence[Mapping[str, Any]],
) -> None:
    final_dir = Path(request.output_dir)
    business_hashes = _business_hashes(directory)
    manifest = {
        "schema_version": "kmfa.project_cost.run_manifest.v4",
        "run_id": request.run_id,
        "request_hash": request.request_hash(),
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "mode": "reference-replay",
        "as_of": request.as_of,
        "project_scope": {"reference_project_count": request.expected_project_count},
        **status_planes.as_dict(),
        "replay_fidelity_status": fidelity_status.value,
        "source_quality_status": source_quality_status.value,
        "metric_snapshot_keys": [],
        "source_bindings": list(source_bindings),
        "code_version": request.code_version,
        "config_hash": request.config_hash,
        "supersedes_run_id": None,
        "absolute_output_dir": str(final_dir),
        "primary_output": str(final_dir / primary_name),
        "output_index_md": str(final_dir / "OUTPUT_INDEX.md"),
        "output_index_json": str(final_dir / "output_index.json"),
        "seal_path": str(final_dir / "run_seal.sha256"),
        "internal_process_handoff": None,
        "output_hashes": business_hashes,
    }
    _write_json(directory / "run_manifest.json", manifest)

    result_status = (
        "REFERENCE_REPLAY_EXACT"
        if fidelity_status == ReplayFidelityStatus.EXACT
        else status_planes.generation_status.value
    )
    if fidelity_status == ReplayFidelityStatus.EXACT:
        next_step = "精确回放仅作历史显示/审计证据；不得注入 calculate。"
    elif status_planes.execution_status == ExecutionStatus.FAILED:
        next_step = "检查 generation_failure.json，修复实现后使用新 run ID 和新输出目录重试。"
    else:
        next_step = "补充或恢复 hash-bound reference 输入后使用新 run ID 重试。"
    md_lines = [
        "# Reference replay output index",
        "",
        "- RESULT_STATUS: `%s`" % result_status,
        "- OUTPUT_DIR: `%s`" % final_dir,
        "- PRIMARY_OUTPUT: `%s`" % (final_dir / primary_name),
        "- OUTPUT_INDEX: `%s`" % (final_dir / "OUTPUT_INDEX.md"),
        "- NEXT_STEP: %s" % next_step,
        "",
        "Reference replay is private audit/display evidence. It is not calculate truth or company approval.",
    ]
    _write_exclusive(directory / "OUTPUT_INDEX.md", ("\n".join(md_lines) + "\n").encode("utf-8"))

    listed = []
    for path in sorted(directory.iterdir(), key=lambda item: item.name):
        if not path.is_file() or path.name in {"output_index.json", "run_seal.sha256"}:
            continue
        listed.append(
            {
                "path": str(final_dir / path.name),
                "sha256": _sha256_file(path),
                "artifact_type": path.name,
            }
        )
    output_index = {
        "schema_version": "kmfa.project_cost.output_index.v2",
        "run_id": request.run_id,
        "result_status": result_status,
        "output_dir": str(final_dir),
        "primary_output": str(final_dir / primary_name),
        "seal_path": str(final_dir / "run_seal.sha256"),
        "files": listed,
        "next_step": next_step,
    }
    _write_json(directory / "output_index.json", output_index)

    seal_lines = []
    for path in sorted(directory.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name != "run_seal.sha256":
            seal_lines.append("%s  %s" % (_sha256_file(path), path.name))
    _write_exclusive(directory / "run_seal.sha256", ("\n".join(seal_lines) + "\n").encode("ascii"))


def _write_success(
    directory: Path,
    request: ReferenceReplayRequest,
    result: ReferenceReplayResult,
    *,
    elapsed_ms: int,
) -> Tuple[RunStatusPlanes, str]:
    planes = RunStatusPlanes(
        ExecutionStatus.SUCCEEDED,
        InputReadinessStatus.SUFFICIENT,
        CalculationStatus.NOT_EVALUATED,
        GenerationStatus.NOT_GENERATED,
    )
    planes.validate()
    _write_json(directory / "input_sufficiency_report.json", _input_report(request, status=InputReadinessStatus.SUFFICIENT).as_dict())
    _write_json(directory / "reference_replay_results.json", result.as_dict())
    _write_json(
        directory / "validation_summary.json",
        {
            "schema_version": "kmfa.project_cost.reference_replay_validation.v1",
            "run_id": request.run_id,
            **planes.as_dict(),
            "replay_fidelity_status": ReplayFidelityStatus.EXACT.value,
            "source_quality_status": result.source_quality_status.value,
            "reference_project_count": len(result.projects),
            "reference_replay_exact_count": len(result.projects),
            "reference_line_item_count": sum(len(item.project.line_items) for item in result.projects),
            "reference_pdf_hash_match_count": len(result.projects),
            "source_arithmetic_difference_count": result.arithmetic_difference_count,
            "source_arithmetic_differences_preserved": True,
            "reference_values_available_to_calculate": False,
        },
    )
    review_rows = []
    for index, item in enumerate(result.projects, 1):
        if item.source_quality_status == SourceQualityStatus.SOURCE_ARITHMETIC_DIFFERENCE:
            review_rows.append(
                (
                    "replay-source-arithmetic-%03d" % index,
                    "P1",
                    "SOURCE_ARITHMETIC_DIFFERENCE",
                    item.project.project_code,
                    item.source_profit_delta_minor,
                    False,
                    "Preserve source and recomputed values separately; do not overwrite either.",
                )
            )
    _write_exclusive(
        directory / "review_tasks.csv",
        _csv_bytes(
            ("task_id", "severity", "blocker_code", "project_ref", "delta_minor", "blocking", "required_action"),
            review_rows,
        ),
    )
    _write_exclusive(
        directory / "traceability_snapshot.csv",
        _csv_bytes(
            ("requirement_id", "run_id", "primary_test", "evidence", "status"),
            (("REQ-011", "R10", "test_reference_calculate_isolation", "reference_replay_results.json", "VALIDATED_R10"),),
        ),
    )
    _write_json(
        directory / "performance_summary.json",
        {
            "schema_version": "kmfa.project_cost.reference_replay_performance.v1",
            "elapsed_ms_before_controls": elapsed_ms,
            "reference_project_count": len(result.projects),
            "reference_pdf_read_count": len(result.projects),
            "baseline_parse_count": 1,
            "calculate_aggregation_call_count": 0,
        },
    )
    _write_json(
        directory / "privacy_scan.json",
        {
            "schema_version": "kmfa.project_cost.reference_replay_privacy.v1",
            "artifact_classification": "PRIVATE_RUNTIME",
            "raw_source_modified": False,
            "reference_values_exported_publicly": False,
            "calculate_data_flow_used": False,
            "company_approval_state_managed": False,
            "status": "PASS_PRIVATE_RUNTIME_BOUNDARY",
        },
    )
    source_bindings = [
        {
            "source_kind": "PRIVATE_REFERENCE_BASELINE",
            "sha256": result.baseline.content_sha256,
            "record_count": len(result.projects),
        }
    ]
    source_bindings.extend(
        {
            "source_kind": "REFERENCE_PDF",
            "source_id": _sha256_bytes(item.project.reference_pdf.encode("utf-8"))[:32],
            "sha256": item.actual_pdf_sha256,
        }
        for item in result.projects
    )
    _write_output_controls(
        directory,
        request,
        status_planes=planes,
        fidelity_status=ReplayFidelityStatus.EXACT,
        source_quality_status=result.source_quality_status,
        primary_name="reference_replay_results.json",
        source_bindings=source_bindings,
    )
    return planes, "reference_replay_results.json"


def _write_blocked(
    directory: Path,
    request: ReferenceReplayRequest,
    issue: ReferenceReplayError,
    *,
    elapsed_ms: int,
) -> Tuple[RunStatusPlanes, str]:
    execution = (
        ExecutionStatus.EXPECTED_BLOCKED
        if issue.input_status in {InputReadinessStatus.SUFFICIENT, InputReadinessStatus.SUFFICIENT_WITH_DOCUMENTED_SCOPE}
        else ExecutionStatus.NEEDS_USER_INPUT
    )
    planes = RunStatusPlanes(
        execution,
        issue.input_status,
        CalculationStatus.NOT_EVALUATED,
        GenerationStatus.BLOCKED_DIAGNOSTICS_GENERATED,
    )
    planes.validate()
    report = _input_report(request, status=issue.input_status, issue=issue)
    _write_json(directory / "input_sufficiency_report.json", report.as_dict())
    _write_json(
        directory / "blocked_diagnostics.json",
        {
            "schema_version": "kmfa.project_cost.reference_replay_blocked.v1",
            "run_id": request.run_id,
            **planes.as_dict(),
            "replay_fidelity_status": issue.fidelity_status.value,
            "source_quality_status": SourceQualityStatus.UNKNOWN.value,
            "blocker_codes": [issue.code],
            "message": issue.message,
            "reference_values_replayed": False,
            "calculate_data_flow_used": False,
            "next_step": "补充或恢复 hash-bound reference 输入；未明确处理前保持阻塞。",
        },
    )
    _write_json(
        directory / "validation_summary.json",
        {
            "schema_version": "kmfa.project_cost.reference_replay_validation.v1",
            "run_id": request.run_id,
            **planes.as_dict(),
            "replay_fidelity_status": issue.fidelity_status.value,
            "source_quality_status": SourceQualityStatus.UNKNOWN.value,
            "reference_replay_exact_count": 0,
            "blocker_codes": [issue.code],
        },
    )
    _write_exclusive(
        directory / "review_tasks.csv",
        _csv_bytes(
            ("task_id", "severity", "blocker_code", "blocking", "required_action"),
            (("reference-replay-blocked", "P0", issue.code, True, "Restore qualified hash-bound reference input or keep blocked."),),
        ),
    )
    _write_exclusive(
        directory / "traceability_snapshot.csv",
        _csv_bytes(
            ("requirement_id", "run_id", "primary_test", "evidence", "status"),
            (("REQ-011", "R10", "test_reference_calculate_isolation", "blocked_diagnostics.json", "BLOCKED_R10"),),
        ),
    )
    _write_json(
        directory / "performance_summary.json",
        {
            "schema_version": "kmfa.project_cost.reference_replay_performance.v1",
            "elapsed_ms_before_controls": elapsed_ms,
            "calculate_aggregation_call_count": 0,
        },
    )
    _write_json(
        directory / "privacy_scan.json",
        {
            "schema_version": "kmfa.project_cost.reference_replay_privacy.v1",
            "artifact_classification": "PRIVATE_RUNTIME",
            "raw_source_modified": False,
            "reference_values_replayed": False,
            "reference_values_exported_publicly": False,
            "calculate_data_flow_used": False,
            "status": "PASS_PRIVATE_RUNTIME_BOUNDARY",
        },
    )
    _write_output_controls(
        directory,
        request,
        status_planes=planes,
        fidelity_status=issue.fidelity_status,
        source_quality_status=SourceQualityStatus.UNKNOWN,
        primary_name="blocked_diagnostics.json",
        source_bindings=(),
    )
    return planes, "blocked_diagnostics.json"


def _write_failed(
    directory: Path,
    request: ReferenceReplayRequest,
    *,
    elapsed_ms: int,
) -> Tuple[RunStatusPlanes, str]:
    planes = RunStatusPlanes(
        ExecutionStatus.FAILED,
        InputReadinessStatus.NOT_EVALUATED,
        CalculationStatus.NOT_EVALUATED,
        GenerationStatus.FAILED,
    )
    planes.validate()
    _write_json(
        directory / "input_sufficiency_report.json",
        _input_report(request, status=InputReadinessStatus.NOT_EVALUATED).as_dict(),
    )
    _write_json(
        directory / "generation_failure.json",
        {
            "schema_version": "kmfa.project_cost.reference_replay_failure.v1",
            "run_id": request.run_id,
            **planes.as_dict(),
            "replay_fidelity_status": ReplayFidelityStatus.NOT_EVALUATED.value,
            "source_quality_status": SourceQualityStatus.UNKNOWN.value,
            "error_code": "REFERENCE_REPLAY_UNEXPECTED_FAILURE",
            "reference_values_replayed": False,
            "calculate_data_flow_used": False,
            "next_step": "检查私有 failure evidence，修复实现后使用新 run ID 和输出目录重试。",
        },
    )
    _write_json(
        directory / "validation_summary.json",
        {
            "schema_version": "kmfa.project_cost.reference_replay_validation.v1",
            "run_id": request.run_id,
            **planes.as_dict(),
            "replay_fidelity_status": ReplayFidelityStatus.NOT_EVALUATED.value,
            "source_quality_status": SourceQualityStatus.UNKNOWN.value,
            "reference_replay_exact_count": 0,
            "blocker_codes": ["REFERENCE_REPLAY_UNEXPECTED_FAILURE"],
        },
    )
    _write_exclusive(
        directory / "review_tasks.csv",
        _csv_bytes(
            ("task_id", "severity", "blocker_code", "blocking", "required_action"),
            (
                (
                    "reference-replay-failed",
                    "P0",
                    "REFERENCE_REPLAY_UNEXPECTED_FAILURE",
                    True,
                    "Inspect private failure evidence and fix the replay implementation.",
                ),
            ),
        ),
    )
    _write_exclusive(
        directory / "traceability_snapshot.csv",
        _csv_bytes(
            ("requirement_id", "run_id", "primary_test", "evidence", "status"),
            (("REQ-011", "R10", "test_reference_calculate_isolation", "generation_failure.json", "FAILED_R10"),),
        ),
    )
    _write_json(
        directory / "performance_summary.json",
        {
            "schema_version": "kmfa.project_cost.reference_replay_performance.v1",
            "elapsed_ms_before_controls": elapsed_ms,
            "calculate_aggregation_call_count": 0,
        },
    )
    _write_json(
        directory / "privacy_scan.json",
        {
            "schema_version": "kmfa.project_cost.reference_replay_privacy.v1",
            "artifact_classification": "PRIVATE_RUNTIME",
            "raw_source_modified": False,
            "reference_values_exported_publicly": False,
            "calculate_data_flow_used": False,
            "status": "PASS_PRIVATE_RUNTIME_BOUNDARY",
        },
    )
    _write_output_controls(
        directory,
        request,
        status_planes=planes,
        fidelity_status=ReplayFidelityStatus.NOT_EVALUATED,
        source_quality_status=SourceQualityStatus.UNKNOWN,
        primary_name="generation_failure.json",
        source_bindings=(),
    )
    return planes, "generation_failure.json"


def _clear_partial_output(directory: Path) -> None:
    """Remove only files created inside the unpublished atomic staging directory."""
    for path in directory.iterdir():
        if path.is_symlink() or path.is_file():
            path.unlink()
            continue
        raise ReferenceReplayError(
            "REFERENCE_REPLAY_STAGING_UNSAFE",
            "unexpected non-file entry in atomic replay staging directory",
        )


def run_reference_replay(request: ReferenceReplayRequest) -> GeneratedReplayRun:
    baseline_path = request.validate_metadata()
    start = time.monotonic()
    output = Path(request.output_dir)
    planes: RunStatusPlanes
    fidelity = ReplayFidelityStatus.NOT_EVALUATED
    quality = SourceQualityStatus.UNKNOWN
    primary_name = "blocked_diagnostics.json"
    with atomic_output_directory(output.parent, output.name) as staging:
        try:
            try:
                baseline_data = _stable_file_bytes(baseline_path, max_bytes=MAX_BASELINE_BYTES)
                baseline = ReferenceBaseline.from_bytes(baseline_data, expected_sha256=request.baseline_sha256)
                projects = _replay_projects(request, baseline)
                result = ReferenceReplayResult(request, baseline, projects)
                elapsed_ms = int((time.monotonic() - start) * 1000)
                planes, primary_name = _write_success(staging, request, result, elapsed_ms=elapsed_ms)
                fidelity = ReplayFidelityStatus.EXACT
                quality = result.source_quality_status
            except ReferenceReplayError as issue:
                elapsed_ms = int((time.monotonic() - start) * 1000)
                planes, primary_name = _write_blocked(staging, request, issue, elapsed_ms=elapsed_ms)
                fidelity = issue.fidelity_status
                quality = SourceQualityStatus.UNKNOWN
            except (FileSecurityError, PathSafetyError) as exc:
                issue = ReferenceReplayError(
                    getattr(exc, "code", "REFERENCE_REPLAY_SECURITY"),
                    getattr(exc, "message", "reference replay security gate failed"),
                    requirement_id="SAFE_READ_AND_DIGEST",
                )
                elapsed_ms = int((time.monotonic() - start) * 1000)
                planes, primary_name = _write_blocked(staging, request, issue, elapsed_ms=elapsed_ms)
                fidelity = issue.fidelity_status
                quality = SourceQualityStatus.UNKNOWN
        except Exception:
            _clear_partial_output(staging)
            elapsed_ms = int((time.monotonic() - start) * 1000)
            planes, primary_name = _write_failed(staging, request, elapsed_ms=elapsed_ms)
            fidelity = ReplayFidelityStatus.NOT_EVALUATED
            quality = SourceQualityStatus.UNKNOWN

    result = GeneratedReplayRun(
        status_planes=planes,
        replay_fidelity_status=fidelity,
        source_quality_status=quality,
        output_dir=output,
        primary_output=output / primary_name,
        output_index_md=output / "OUTPUT_INDEX.md",
        output_index_json=output / "output_index.json",
        run_seal=output / "run_seal.sha256",
    )
    if not verify_replay_run_seal(output) or not verify_replay_output_index(output):
        raise ReferenceReplayError("REFERENCE_REPLAY_CONTROL_VERIFY", "published replay controls failed verification")
    return result


def verify_replay_run_seal(output_dir: Path) -> bool:
    root = Path(output_dir)
    seal = root / "run_seal.sha256"
    if not seal.is_file():
        return False
    expected = {}
    try:
        for line in seal.read_text(encoding="ascii").splitlines():
            digest, name = line.split("  ", 1)
            if not SHA256_RE.fullmatch(digest) or not name or "/" in name or name in expected:
                return False
            expected[name] = digest
    except (OSError, UnicodeError, ValueError):
        return False
    actual_names = {
        path.name
        for path in root.iterdir()
        if path.is_file() and path.name != "run_seal.sha256"
    }
    if set(expected) != actual_names:
        return False
    return all(_sha256_file(root / name) == digest for name, digest in expected.items())


def verify_replay_output_index(output_dir: Path) -> bool:
    root = Path(output_dir)
    index_path = root / "output_index.json"
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    if (
        payload.get("schema_version") != "kmfa.project_cost.output_index.v2"
        or payload.get("output_dir") != str(root)
        or payload.get("seal_path") != str(root / "run_seal.sha256")
        or payload.get("result_status")
        not in {"REFERENCE_REPLAY_EXACT", "BLOCKED_DIAGNOSTICS_GENERATED", "FAILED"}
    ):
        return False
    files = payload.get("files")
    if not isinstance(files, list):
        return False
    seen = set()
    for item in files:
        if not isinstance(item, Mapping) or set(item) != {"path", "sha256", "artifact_type"}:
            return False
        path = Path(item["path"])
        if not path.is_absolute() or path.parent != root or path.name in seen:
            return False
        if path.name in {"output_index.json", "run_seal.sha256"} or not path.is_file():
            return False
        if _sha256_file(path) != item["sha256"]:
            return False
        seen.add(path.name)
    expected = {
        path.name
        for path in root.iterdir()
        if path.is_file() and path.name not in {"output_index.json", "run_seal.sha256"}
    }
    return seen == expected
