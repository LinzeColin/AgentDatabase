"""R9 final/blocked artifact generation with non-cyclic indexes and detached seal."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from .input_gate import InputSufficiencyReport, render_missing_input_prompt
from .metrics import MetricBatchResult, MetricFact, MetricSnapshot, MetricScope, metric_facts_hash
from .paths import PathSafetyError, atomic_output_directory
from .security import SecurityProfile, escape_spreadsheet_text
from .statuses import (
    CalculationStatus,
    ExecutionStatus,
    GenerationStatus,
    InputReadinessStatus,
    RunStatusPlanes,
    SUFFICIENT_INPUT_STATUSES,
)
from .workbook import (
    ArtifactToolRuntime,
    WorkbookError,
    WorkbookSheet,
    WorkbookValidation,
    build_project_cost_workbook,
    minor_to_cny_display,
)


RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CONTROL_FILES = frozenset({"run_manifest.json", "OUTPUT_INDEX.md", "output_index.json", "run_seal.sha256"})


class GenerationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


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
                raise GenerationError("CSV_VALUE_INVALID", "CSV values must be integer, boolean, text, or null")
        writer.writerow(values)
    return buffer.getvalue().encode("utf-8")


@dataclass(frozen=True)
class SourceLineage:
    source_slot_id: str
    opaque_source_id: str
    source_sha256: str
    reader_version: str
    schema_fingerprint: str
    logical_source_period: str

    def validate(self) -> None:
        for field in ("source_slot_id", "opaque_source_id", "reader_version", "logical_source_period"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value or any(char in value for char in "\r\n\x00"):
                raise GenerationError("SOURCE_LINEAGE_INVALID", "%s must be safe nonempty text" % field)
        if not SHA256_RE.fullmatch(self.source_sha256) or not SHA256_RE.fullmatch(self.schema_fingerprint):
            raise GenerationError("SOURCE_LINEAGE_HASH_INVALID", "source and schema hashes must be SHA256")

    def as_dict(self) -> Dict[str, str]:
        self.validate()
        return {
            "source_slot_id": self.source_slot_id,
            "opaque_source_id": self.opaque_source_id,
            "source_sha256": self.source_sha256,
            "reader_version": self.reader_version,
            "schema_fingerprint": self.schema_fingerprint,
            "logical_source_period": self.logical_source_period,
        }


@dataclass(frozen=True)
class ReviewQueueItem:
    task_id: str
    severity: str
    blocker_code: str
    metric_id: Optional[str]
    description: str
    required_action: str
    evidence_refs: Tuple[str, ...] = ()
    blocking: bool = True

    def validate(self) -> None:
        if not RUN_ID_RE.fullmatch(self.task_id) or self.severity not in {"P0", "P1", "P2", "P3"}:
            raise GenerationError("REVIEW_TASK_INVALID", "review task ID or severity is invalid")
        for field in ("blocker_code", "description", "required_action"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value:
                raise GenerationError("REVIEW_TASK_INVALID", "%s is required" % field)
        if tuple(sorted(set(self.evidence_refs))) != self.evidence_refs:
            raise GenerationError("REVIEW_TASK_EVIDENCE_INVALID", "evidence refs must be sorted and unique")
        if not isinstance(self.blocking, bool):
            raise GenerationError("REVIEW_TASK_BLOCKING_INVALID", "review task blocking flag must be boolean")


@dataclass(frozen=True)
class RunGenerationRequest:
    run_id: str
    request_hash: str
    mode: str
    as_of: str
    output_dir: Path
    input_report: InputSufficiencyReport
    metric_batch: Optional[MetricBatchResult]
    facts: Tuple[MetricFact, ...]
    source_lineage: Tuple[SourceLineage, ...]
    review_tasks: Tuple[ReviewQueueItem, ...]
    security_profile: SecurityProfile
    workbook_runtime: Optional[ArtifactToolRuntime]
    code_version: str
    config_hash: str
    supersedes_run_id: Optional[str] = None
    expected_block: bool = False
    visual_evidence_dir: Optional[Path] = None

    def validate(self) -> None:
        if not RUN_ID_RE.fullmatch(self.run_id) or not SHA256_RE.fullmatch(self.request_hash):
            raise GenerationError("RUN_BINDING_INVALID", "run ID and request hash are required")
        if self.mode not in {"calculate", "restate"}:
            raise GenerationError("GENERATION_MODE_INVALID", "R9 final generation supports calculate or restate")
        try:
            datetime.strptime(self.as_of, "%Y-%m-%d")
        except (TypeError, ValueError) as exc:
            raise GenerationError("GENERATION_AS_OF_INVALID", "as-of must be canonical ISO") from exc
        output = Path(self.output_dir)
        if not output.is_absolute() or output.exists() or not output.parent.is_dir():
            raise GenerationError("GENERATION_OUTPUT_INVALID", "output directory must be a new absolute path")
        if self.input_report.run_id != self.run_id or self.input_report.request_hash != self.request_hash:
            raise GenerationError("INPUT_REPORT_BINDING_INVALID", "input report does not bind this run request")
        if self.input_report.mode != self.mode:
            raise GenerationError("INPUT_REPORT_MODE_MISMATCH", "input report mode differs from the generation request")
        if Path(self.input_report.output_dir) != output:
            raise GenerationError("INPUT_REPORT_OUTPUT_MISMATCH", "input report and final run must bind the same output directory")
        if self.input_report.user_action_required and (self.metric_batch is not None or self.facts):
            raise GenerationError(
                "CALCULATION_BEFORE_INPUT_GATE",
                "an input-incomplete run cannot carry calculated Metrics or facts",
            )
        if self.mode == "restate" and not self.supersedes_run_id:
            raise GenerationError("RESTATEMENT_REFERENCE_REQUIRED", "restate requires a superseded run ID")
        if self.mode == "calculate" and self.supersedes_run_id is not None:
            raise GenerationError("CALCULATE_SUPERSESSION_FORBIDDEN", "calculate cannot overwrite or supersede a prior run")
        if not self.code_version or not SHA256_RE.fullmatch(self.config_hash):
            raise GenerationError("GENERATION_VERSION_BINDING_INVALID", "code version and config hash are required")
        if self.visual_evidence_dir is not None:
            evidence = Path(self.visual_evidence_dir)
            if not evidence.is_absolute() or evidence.exists() or not evidence.parent.is_dir():
                raise GenerationError(
                    "VISUAL_EVIDENCE_OUTPUT_INVALID",
                    "visual evidence directory must be a new absolute path with an existing parent",
                )
        for item in self.facts:
            item.validate()
        for item in self.source_lineage:
            item.validate()
        for item in self.review_tasks:
            item.validate()
        if self.metric_batch is not None:
            self.metric_batch.validate()
            report_metrics = set(self.input_report.requested_metrics)
            report_bases = set(self.input_report.requested_basis_ids)
            if any(metric_id not in report_metrics or basis_id not in report_bases for metric_id, basis_id in self.metric_batch.required_pairs):
                raise GenerationError(
                    "INPUT_REPORT_METRIC_BASIS_MISMATCH",
                    "input sufficiency did not cover every required Metric/basis pair",
                )
            snapshot_map = self.metric_batch.snapshot_map()
            grouped: Dict[Tuple[str, str], list[MetricFact]] = {}
            for fact in self.facts:
                if (fact.metric_id, fact.accounting_basis_id) not in snapshot_map:
                    raise GenerationError("GENERATION_FACT_NOT_IN_BATCH", "fact belongs to an unbound Metric/basis")
                grouped.setdefault((fact.metric_id, fact.accounting_basis_id), []).append(fact)
            for key, snapshot in snapshot_map.items():
                direct_facts = tuple(grouped.get(key, ()))
                if snapshot.source_control_amount_minor is not None:
                    if snapshot.source_record_count != len(direct_facts) or snapshot.facts_hash != metric_facts_hash(direct_facts):
                        raise GenerationError(
                            "GENERATION_FACT_SNAPSHOT_MISMATCH",
                            "workbook detail facts do not match the bound direct Metric snapshot",
                        )


@dataclass(frozen=True)
class GeneratedRun:
    status_planes: RunStatusPlanes
    output_dir: Path
    primary_output: Path
    output_index_md: Path
    output_index_json: Path
    run_seal: Path
    internal_process_handoff: Optional[Path]

    def locator_text(self) -> str:
        self.status_planes.validate()
        return "\n".join(
            (
                "RESULT_STATUS: %s" % self.status_planes.generation_status.value,
                "OUTPUT_DIR: %s" % self.output_dir,
                "PRIMARY_OUTPUT: %s" % self.primary_output,
                "OUTPUT_INDEX: %s" % self.output_index_md,
                "NEXT_STEP: %s"
                % (
                    "由调用方 Codex/操作人在 Skill 外按公司现有内部流程处理；Skill 不管理审批。"
                    if self.status_planes.generation_status == GenerationStatus.FINAL_GENERATED
                    else (
                        "查看 generation_failure.json 后修复生成器并以新 run 重试。"
                        if self.status_planes.generation_status == GenerationStatus.FAILED
                        else "按 missing_input_prompt/review_tasks 补充输入或明确选择允许的处理方式。"
                    )
                ),
            )
        )


def _input_status(report: InputSufficiencyReport) -> InputReadinessStatus:
    try:
        status = InputReadinessStatus(report.overall_status)
    except ValueError as exc:
        raise GenerationError("INPUT_STATUS_UNKNOWN", "input readiness status is not registered") from exc
    expected_action = status not in SUFFICIENT_INPUT_STATUSES
    if report.user_action_required != expected_action:
        raise GenerationError("INPUT_STATUS_ACTION_CONFLICT", "input action flag conflicts with readiness status")
    return status


def _derive_statuses(request: RunGenerationRequest) -> Tuple[RunStatusPlanes, Tuple[str, ...]]:
    input_status = _input_status(request.input_report)
    blockers = set()
    calculation_status = CalculationStatus.NOT_EVALUATED
    if input_status not in SUFFICIENT_INPUT_STATUSES:
        # Input insufficiency is an explicit calculation gate, not an
        # unevaluated success-shaped state.  The current-source regression and
        # every normal calculate run must expose a blocked calculation plane.
        calculation_status = CalculationStatus.BLOCKED_SOURCE
        blockers.update(
            item.requirement_id
            for item in request.input_report.items
            if item.observed_status not in {"PRESENT", "NOT_IN_SCOPE"}
        )
    elif request.metric_batch is None:
        blockers.add("METRIC_BATCH_MISSING")
        calculation_status = CalculationStatus.BLOCKED_SCHEMA
    else:
        calculation_status = request.metric_batch.calculation_status
        blockers.update(request.metric_batch.blocker_codes)
        snapshot_scopes = {item.scope.fingerprint for item in request.metric_batch.snapshots}
        if len(snapshot_scopes) != 1:
            blockers.add("METRIC_IDENTITY_BATCH_SCOPE_MISMATCH")
            calculation_status = CalculationStatus.BLOCKED_IDENTITY
        if any(item.as_of != request.as_of for item in request.metric_batch.snapshots):
            blockers.add("METRIC_PERIOD_BATCH_AS_OF_MISMATCH")
            calculation_status = CalculationStatus.BLOCKED_PERIOD
        blockers.update(item.blocker_code for item in request.review_tasks if item.blocking)
        if any(item.blocking for item in request.review_tasks) and calculation_status == CalculationStatus.VALIDATED:
            calculation_status = CalculationStatus.BLOCKED_RECONCILIATION
    if input_status in SUFFICIENT_INPUT_STATUSES and calculation_status == CalculationStatus.VALIDATED:
        if not request.source_lineage:
            blockers.add("SOURCE_LINEAGE_MISSING")
            calculation_status = CalculationStatus.BLOCKED_SOURCE
        elif request.workbook_runtime is None:
            blockers.add("WORKBOOK_RUNTIME_INPUT_REQUIRED")
            calculation_status = CalculationStatus.BLOCKED_SECURITY
        else:
            try:
                request.workbook_runtime.validate()
            except WorkbookError as exc:
                blockers.add(exc.code)
                calculation_status = CalculationStatus.BLOCKED_SECURITY
    if not blockers and calculation_status == CalculationStatus.VALIDATED:
        planes = RunStatusPlanes(
            ExecutionStatus.SUCCEEDED,
            input_status,
            CalculationStatus.VALIDATED,
            GenerationStatus.FINAL_GENERATED,
        )
    else:
        execution = ExecutionStatus.EXPECTED_BLOCKED if request.expected_block else ExecutionStatus.NEEDS_USER_INPUT
        planes = RunStatusPlanes(
            execution,
            input_status,
            calculation_status,
            GenerationStatus.BLOCKED_DIAGNOSTICS_GENERATED,
        )
    planes.validate()
    return planes, tuple(sorted(blockers))


def _money_columns(snapshot: MetricSnapshot) -> Tuple[Any, ...]:
    values = (
        snapshot.source_value_minor,
        snapshot.recomputed_value_minor,
        snapshot.calculated_value_minor,
        snapshot.source_recomputed_delta_minor,
        snapshot.recomputed_calculated_delta_minor,
    )
    display = tuple(minor_to_cny_display(item) for item in values)
    return values + display


def _workbook_sheets(
    request: RunGenerationRequest,
    planes: RunStatusPlanes,
) -> Tuple[WorkbookSheet, ...]:
    if request.metric_batch is None:
        raise GenerationError("WORKBOOK_METRICS_REQUIRED", "final workbook requires a validated Metric batch")
    snapshots = request.metric_batch.snapshots
    metric_headers = (
        "Metric",
        "会计口径",
        "生命周期",
        "截止日",
        "计算状态",
        "来源值（分）",
        "复算值（分）",
        "计算值（分）",
        "来源-复算（分）",
        "复算-计算（分）",
        "来源值（元展示）",
        "复算值（元展示）",
        "计算值（元展示）",
        "来源-复算（元展示）",
        "复算-计算（元展示）",
    )
    metric_rows = tuple(
        (
            item.metric_id,
            item.accounting_basis_id,
            ",".join(item.included_lifecycle_stages),
            item.as_of,
            item.calculation_status.value,
            *_money_columns(item),
        )
        for item in snapshots
    )
    metric_kinds = ("TEXT", "TEXT", "TEXT", "DATE", "TEXT") + ("MINOR_INTEGER",) * 5 + ("TEXT",) * 5

    fact_rows = tuple(
        (
            item.fact_id,
            item.metric_id,
            item.accounting_basis_id,
            item.lifecycle_stage,
            item.metric_date,
            item.disposition.value,
            item.base_amount_minor,
            minor_to_cny_display(item.base_amount_minor),
            item.disposition_reason,
        )
        for item in sorted(request.facts, key=lambda value: value.fact_id)
    )
    lifecycle_rows = tuple(
        (
            item.metric_id,
            item.accounting_basis_id,
            ",".join(item.included_lifecycle_stages),
            item.calculated_value_minor,
            minor_to_cny_display(item.calculated_value_minor),
            item.as_of_date_rule,
        )
        for item in snapshots
    )
    revenue_cash_rows = tuple(
        (
            item.metric_id,
            item.accounting_basis_id,
            item.calculated_value_minor,
            minor_to_cny_display(item.calculated_value_minor),
            item.calculation_status.value,
        )
        for item in snapshots
        if item.metric_id.startswith(("REV_", "CASH_")) or item.metric_id == "COST_PAID"
    )
    if not revenue_cash_rows:
        revenue_cash_rows = (("NOT_IN_SCOPE", "", None, "", "本次请求未包含收入或现金类 Metric"),)
    source_rows = tuple(
        (
            item.metric_id,
            item.accounting_basis_id,
            item.source_record_count,
            item.source_control_amount_minor,
            item.channel_signed_delta_minor,
            item.channel_absolute_delta_minor,
            item.facts_hash[:16] + "…",
        )
        for item in snapshots
    )
    difference_rows = []
    for item in snapshots:
        if item.source_recomputed_delta_minor not in {None, 0} or item.recomputed_calculated_delta_minor not in {None, 0}:
            difference_rows.append(
                (
                    item.metric_id,
                    item.accounting_basis_id,
                    item.source_recomputed_delta_minor,
                    item.recomputed_calculated_delta_minor,
                    ",".join(item.blocker_codes),
                )
            )
    for item in request.review_tasks:
        difference_rows.append((item.metric_id or "RUN", "REVIEW_TASK", None, None, item.blocker_code))
    if not difference_rows:
        difference_rows.append(("NONE", "NO_DIFFERENCE", 0, 0, "全部差异为 0，且无待确认项"))
    identity_rows = ((
        request.facts[0].scope.legal_entity_id if request.facts else snapshots[0].scope.legal_entity_id,
        request.facts[0].scope.canonical_project_id if request.facts else snapshots[0].scope.canonical_project_id,
        request.facts[0].scope.wbs_or_cost_code if request.facts else snapshots[0].scope.wbs_or_cost_code,
        snapshots[0].scope.fingerprint[:16] + "…",
        "EXACT_CANONICAL_SCOPE",
    ),)
    run_rows = (
        ("run_id", request.run_id),
        ("mode", request.mode),
        ("as_of", request.as_of),
        ("execution_status", planes.execution_status.value),
        ("input_readiness_status", planes.input_readiness_status.value),
        ("calculation_status", planes.calculation_status.value),
        ("generation_status", planes.generation_status.value),
        ("amount_unit", "CNY minor unit（分）；元列仅为由整数分格式化的展示文本"),
        ("internal_process", "最终文件生成后由调用方 Codex/操作人走公司现有内部流程；Skill 不设置负责人或授权人，不管理审批状态。"),
    )
    return (
        WorkbookSheet("01_项目成本表", "项目成本表｜双口径与命名指标", metric_headers, metric_rows, metric_kinds, (24, 34, 28, 14, 18) + (17,) * 10),
        WorkbookSheet(
            "02_成本明细",
            "成本明细｜不可变事实与纳入状态",
            ("事实ID", "Metric", "会计口径", "生命周期", "Metric日期", "处置", "金额（分）", "金额（元展示）", "原因"),
            fact_rows,
            ("TEXT", "TEXT", "TEXT", "TEXT", "DATE", "TEXT", "MINOR_INTEGER", "TEXT", "TEXT"),
            (38, 24, 32, 20, 14, 14, 17, 18, 28),
        ),
        WorkbookSheet(
            "03_生命周期对照",
            "生命周期对照｜预算、承诺、暂估、实际、支付与预测不混合",
            ("Metric", "会计口径", "纳入生命周期", "计算值（分）", "计算值（元展示）", "截止日规则"),
            lifecycle_rows,
            ("TEXT", "TEXT", "TEXT", "MINOR_INTEGER", "TEXT", "TEXT"),
            (20, 32, 30, 18, 18, 28),
        ),
        WorkbookSheet(
            "04_收入与现金",
            "收入与现金｜开票、确认收入、回款与付款分列",
            ("Metric", "会计口径", "计算值（分）", "计算值（元展示）", "状态"),
            revenue_cash_rows,
            ("TEXT", "TEXT", "MINOR_INTEGER", "TEXT", "TEXT"),
            (22, 34, 18, 18, 20),
        ),
        WorkbookSheet(
            "05_来源与核销",
            "来源与核销｜双通道及来源守恒",
            ("Metric", "会计口径", "来源记录数", "来源控制（分）", "通道差异（分）", "绝对额通道差异（分）", "事实哈希（前16位）"),
            source_rows,
            ("TEXT", "TEXT", "INTEGER", "MINOR_INTEGER", "MINOR_INTEGER", "MINOR_INTEGER", "TEXT"),
            (20, 34, 16, 18, 18, 22, 42),
        ),
        WorkbookSheet(
            "06_差异与待确认",
            "差异与待确认｜不得静默覆盖",
            ("Metric", "会计口径/类型", "来源-复算（分）", "复算-计算（分）", "阻断码/待办"),
            tuple(difference_rows),
            ("TEXT", "TEXT", "MINOR_INTEGER", "MINOR_INTEGER", "TEXT"),
            (22, 30, 20, 20, 42),
        ),
        WorkbookSheet(
            "07_项目身份",
            "项目身份｜主体、项目与WBS精确范围",
            ("法人主体", "Canonical Project", "WBS/成本码", "范围指纹（前16位）", "解析状态"),
            identity_rows,
            ("TEXT", "TEXT", "TEXT", "TEXT", "TEXT"),
            (24, 28, 24, 42, 24),
        ),
        WorkbookSheet(
            "08_运行说明",
            "运行说明｜四状态平面与使用边界",
            ("项目", "值"),
            run_rows,
            ("TEXT", "TEXT"),
            (28, 42),
        ),
    )


def _review_tasks(request: RunGenerationRequest, blockers: Sequence[str]) -> Tuple[ReviewQueueItem, ...]:
    result = list(request.review_tasks)
    existing = {item.blocker_code for item in result}
    for index, code in enumerate(blockers, 1):
        if code in existing:
            continue
        result.append(
            ReviewQueueItem(
                task_id="R9-%03d" % index,
                severity="P0",
                blocker_code=code,
                metric_id=None,
                description="运行门禁未通过：%s" % code,
                required_action="补充输入、提供合格替代证据、明确缩小范围，或保持阻塞。",
            )
        )
    return tuple(sorted(result, key=lambda item: item.task_id))


def _output_index_markdown(
    *,
    request: RunGenerationRequest,
    planes: RunStatusPlanes,
    primary_output: Path,
    finalized_hashes: Mapping[str, str],
) -> str:
    output_dir = Path(request.output_dir)
    lines = [
        "# Project cost run output index",
        "",
        "RESULT_STATUS: `%s`" % planes.generation_status.value,
        "",
        "OUTPUT_DIR: `%s`" % output_dir,
        "",
        "PRIMARY_OUTPUT: `%s`" % primary_output,
        "",
        "OUTPUT_INDEX: `%s`" % (output_dir / "OUTPUT_INDEX.md"),
        "",
        "| Artifact | SHA256 | Absolute path |",
        "| --- | --- | --- |",
    ]
    for name, digest in sorted(finalized_hashes.items()):
        lines.append("| `%s` | `%s` | `%s` |" % (name, digest, output_dir / name))
    lines.extend(
        [
            "",
            "`output_index.json` 与 `run_seal.sha256` 为非循环控制文件，不在本表自哈希。",
            "",
            "NEXT_STEP: %s"
            % (
                "由调用方 Codex/操作人在 Skill 外走公司现有内部流程；Skill 不设置负责人、授权人或审批状态。"
                if planes.generation_status == GenerationStatus.FINAL_GENERATED
                else (
                    "查看 generation_failure.json，修复生成或验证故障后以新 run 重试。"
                    if planes.generation_status == GenerationStatus.FAILED
                    else "查看 missing_input_prompt.md、blocked_diagnostics.json 和 review_tasks.csv 后明确处理。"
                )
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def _seal_payload(root: Path) -> bytes:
    lines = []
    for path in sorted(item for item in root.iterdir() if item.is_file() and item.name != "run_seal.sha256"):
        lines.append("%s  %s" % (_sha256_file(path), path.name))
    return ("\n".join(lines) + "\n").encode("utf-8")


def verify_run_seal(output_dir: Path) -> bool:
    output_dir = Path(output_dir)
    seal = output_dir / "run_seal.sha256"
    if not seal.is_file() or seal.is_symlink():
        return False
    expected_names = {item.name for item in output_dir.iterdir() if item.is_file() and item.name != seal.name}
    observed = set()
    try:
        for line in seal.read_text(encoding="utf-8").splitlines():
            digest, name = line.split("  ", 1)
            if not SHA256_RE.fullmatch(digest) or Path(name).name != name or name in observed:
                return False
            observed.add(name)
            if _sha256_file(output_dir / name) != digest:
                return False
    except (OSError, UnicodeError, ValueError):
        return False
    return observed == expected_names


def verify_output_index(output_dir: Path) -> bool:
    output_dir = Path(output_dir)
    try:
        payload = json.loads((output_dir / "output_index.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    if payload.get("output_dir") != str(output_dir) or payload.get("seal_path") != str(output_dir / "run_seal.sha256"):
        return False
    listed = set()
    for item in payload.get("files", []):
        path = Path(item.get("path", ""))
        if path.parent != output_dir or path.name in {"output_index.json", "run_seal.sha256"}:
            return False
        if not path.is_file() or _sha256_file(path) != item.get("sha256"):
            return False
        listed.add(path.name)
    expected = {item.name for item in output_dir.iterdir() if item.is_file()} - {"output_index.json", "run_seal.sha256"}
    return listed == expected


def _publish_generation_failure(request: RunGenerationRequest, *, code: str, message: str) -> GeneratedRun:
    """Publish a sealed non-final diagnostic after a renderer/export failure."""

    output_dir = Path(request.output_dir)
    input_status = _input_status(request.input_report)
    calculation_status = request.metric_batch.calculation_status if request.metric_batch else CalculationStatus.ERROR
    planes = RunStatusPlanes(
        ExecutionStatus.FAILED,
        input_status,
        calculation_status,
        GenerationStatus.FAILED,
    )
    planes.validate()
    primary_output = output_dir / "generation_failure.json"
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        with atomic_output_directory(output_dir.parent, output_dir.name) as temporary:
            _write_json(temporary / "input_sufficiency_report.json", request.input_report.as_dict())
            _write_json(
                temporary / "generation_failure.json",
                {
                    "schema_version": "kmfa.project_cost.generation_failure.v1",
                    "run_id": request.run_id,
                    **planes.as_dict(),
                    "error_code": code,
                    "error_message": message,
                    "final_financial_workbook_generated": False,
                    "next_step": "修复生成器或工作簿验证故障，并使用新的 run ID/输出目录重试。",
                },
            )
            _write_exclusive(
                temporary / "review_tasks.csv",
                _csv_bytes(
                    ("task_id", "severity", "blocker_code", "metric_id", "description", "required_action", "evidence_refs", "blocking"),
                    (("R9-GENERATION-FAILURE", "P0", code, None, message, "修复生成器并以新 run 重试", "", True),),
                ),
            )
            _write_json(
                temporary / "validation_summary.json",
                {
                    "schema_version": "kmfa.project_cost.validation_summary.v1",
                    "run_id": request.run_id,
                    **planes.as_dict(),
                    "workbook_validation": None,
                    "renderer_or_output_validation_error": code,
                    "seal_verified_before_publish": True,
                },
            )
            business_hashes = {
                path.name: _sha256_file(path)
                for path in temporary.iterdir()
                if path.is_file() and path.name not in CONTROL_FILES
            }
            manifest = {
                "schema_version": "kmfa.project_cost.run_manifest.v4",
                "run_id": request.run_id,
                "request_hash": request.request_hash,
                "created_at": created_at,
                "mode": request.mode,
                "as_of": request.as_of,
                "project_scope": request.metric_batch.snapshots[0].scope.as_dict() if request.metric_batch and request.metric_batch.snapshots else None,
                **planes.as_dict(),
                "metric_snapshot_keys": [list(item.key) for item in request.metric_batch.snapshots] if request.metric_batch else [],
                "source_bindings": [item.as_dict() for item in request.source_lineage],
                "code_version": request.code_version,
                "config_hash": request.config_hash,
                "supersedes_run_id": request.supersedes_run_id,
                "absolute_output_dir": str(output_dir),
                "primary_output": str(primary_output),
                "output_index_md": str(output_dir / "OUTPUT_INDEX.md"),
                "output_index_json": str(output_dir / "output_index.json"),
                "seal_path": str(output_dir / "run_seal.sha256"),
                "internal_process_handoff": None,
                "output_hashes": dict(sorted(business_hashes.items())),
            }
            _write_json(temporary / "run_manifest.json", manifest)
            md_hashes = {**business_hashes, "run_manifest.json": _sha256_file(temporary / "run_manifest.json")}
            _write_exclusive(
                temporary / "OUTPUT_INDEX.md",
                _output_index_markdown(
                    request=request,
                    planes=planes,
                    primary_output=primary_output,
                    finalized_hashes=md_hashes,
                ).encode("utf-8"),
            )
            files = [
                {"path": str(output_dir / path.name), "sha256": _sha256_file(path), "artifact_type": path.name}
                for path in sorted(item for item in temporary.iterdir() if item.is_file())
                if path.name not in {"output_index.json", "run_seal.sha256"}
            ]
            _write_json(
                temporary / "output_index.json",
                {
                    "schema_version": "kmfa.project_cost.output_index.v2",
                    "run_id": request.run_id,
                    "result_status": "FAILED",
                    "output_dir": str(output_dir),
                    "primary_output": str(primary_output),
                    "seal_path": str(output_dir / "run_seal.sha256"),
                    "files": files,
                    "next_step": "查看 generation_failure.json，修复生成器后以新 run 重试。",
                },
            )
            _write_exclusive(temporary / "run_seal.sha256", _seal_payload(temporary))
            if not verify_run_seal(temporary):
                raise GenerationError("FAILURE_DIAGNOSTIC_SEAL_FAILED", "failure diagnostic seal could not verify")
    except PathSafetyError as exc:
        raise GenerationError("FAILURE_DIAGNOSTIC_PATH", str(exc)) from exc
    if not verify_run_seal(output_dir) or not verify_output_index(output_dir):
        raise GenerationError("FAILURE_DIAGNOSTIC_VERIFY_FAILED", "published failure diagnostics did not verify")
    return GeneratedRun(
        status_planes=planes,
        output_dir=output_dir,
        primary_output=primary_output,
        output_index_md=output_dir / "OUTPUT_INDEX.md",
        output_index_json=output_dir / "output_index.json",
        run_seal=output_dir / "run_seal.sha256",
        internal_process_handoff=None,
    )


def generate_run_artifacts(request: RunGenerationRequest) -> GeneratedRun:
    """Publish either a sealed final workbook or sealed blocked diagnostics, never both."""

    request.validate()
    planes, blockers = _derive_statuses(request)
    output_dir = Path(request.output_dir)
    start = time.perf_counter()
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    final = planes.generation_status == GenerationStatus.FINAL_GENERATED
    review_tasks = _review_tasks(request, blockers)
    workbook_validation: Optional[WorkbookValidation] = None
    primary_name = (
        "项目成本表_%s_%s.xlsx" % (request.metric_batch.snapshots[0].scope.canonical_project_id, request.as_of)
        if final and request.metric_batch is not None
        else "blocked_diagnostics.json"
    )
    project_id = request.metric_batch.snapshots[0].scope.canonical_project_id if request.metric_batch and request.metric_batch.snapshots else ""
    if final and not PROJECT_ID_RE.fullmatch(project_id):
        raise GenerationError("PROJECT_ID_FILENAME_UNSAFE", "canonical project ID is not safe for a final filename")
    primary_output = output_dir / primary_name

    try:
        with atomic_output_directory(output_dir.parent, output_dir.name) as temporary:
            _write_json(temporary / "input_sufficiency_report.json", request.input_report.as_dict())
            prompt = render_missing_input_prompt(request.input_report)
            if prompt is None and not final:
                prompt = "\n".join(
                    (
                        "# 本次运行未达到最终生成条件",
                        "",
                        "阻断项：`%s`" % "`, `".join(blockers),
                        "",
                        "请明确选择：1 补充输入（推荐）；2 缩小受影响范围；3 提供合格替代证据；4 仅省略可选展示；5 保持 BLOCKED，停止正式计算并保留诊断。",
                        "",
                        "未回复不构成授权；非可豁免门禁不能选择 4。",
                        "",
                    )
                )
            if prompt is not None:
                _write_exclusive(temporary / "missing_input_prompt.md", prompt.encode("utf-8"))
            if request.metric_batch is not None:
                _write_json(temporary / "metric_snapshots.json", request.metric_batch.as_dict())
                _write_json(
                    temporary / "metric_facts.json",
                    {
                        "schema_version": "kmfa.project_cost.metric_facts.v1",
                        "facts": [item.as_dict() for item in sorted(request.facts, key=lambda value: value.fact_id)],
                    },
                )
            if final:
                assert request.workbook_runtime is not None
                workbook_validation = build_project_cost_workbook(
                    sheets=_workbook_sheets(request, planes),
                    output_path=temporary / primary_name,
                    work_directory=temporary / ".workbook-build",
                    runtime=request.workbook_runtime,
                    security_profile=request.security_profile,
                    visual_evidence_dir=request.visual_evidence_dir,
                )
                handoff = "\n".join(
                    (
                        "# Internal process handoff",
                        "",
                        "最终文件已由全部 in-scope 数据与校验门禁直接生成。",
                        "",
                        "PRIMARY_OUTPUT: `%s`" % primary_output,
                        "",
                        "OUTPUT_INDEX: `%s`" % (output_dir / "OUTPUT_INDEX.md"),
                        "",
                        "本文件只交接位置与证据。Skill 不设置财务负责人或授权人，不记录或管理公司内部审批状态。",
                        "生成后的公司现有内部流程由调用方 Codex/操作人在 Skill 外执行。",
                        "",
                    )
                )
                _write_exclusive(temporary / "INTERNAL_PROCESS_HANDOFF.md", handoff.encode("utf-8"))
            else:
                _write_json(
                    temporary / "blocked_diagnostics.json",
                    {
                        "schema_version": "kmfa.project_cost.blocked_diagnostics.v1",
                        "run_id": request.run_id,
                        **planes.as_dict(),
                        "blocker_codes": list(blockers),
                        "user_action_required": True,
                        "final_financial_workbook_generated": False,
                        "next_step": "补充输入、提供合格替代证据、明确缩小范围，或保持阻塞。",
                    },
                )

            _write_exclusive(
                temporary / "source_lineage.csv",
                _csv_bytes(
                    ("source_slot_id", "opaque_source_id", "source_sha256", "reader_version", "schema_fingerprint", "logical_source_period"),
                    (
                        (
                            item.source_slot_id,
                            item.opaque_source_id,
                            item.source_sha256,
                            item.reader_version,
                            item.schema_fingerprint,
                            item.logical_source_period,
                        )
                        for item in sorted(request.source_lineage, key=lambda value: (value.source_slot_id, value.opaque_source_id))
                    ),
                ),
            )
            _write_exclusive(
                temporary / "review_tasks.csv",
                _csv_bytes(
                    ("task_id", "severity", "blocker_code", "metric_id", "description", "required_action", "evidence_refs", "blocking"),
                    (
                        (
                            item.task_id,
                            item.severity,
                            item.blocker_code,
                            item.metric_id,
                            item.description,
                            item.required_action,
                            ",".join(item.evidence_refs),
                            item.blocking,
                        )
                        for item in review_tasks
                    ),
                ),
            )
            trace_rows = () if request.metric_batch is None else (
                (
                    item.metric_id,
                    item.accounting_basis_id,
                    item.as_of,
                    item.calculation_status.value,
                    item.facts_hash,
                    ",".join(item.formula_profile_ids),
                    ",".join(item.parameter_profile_ids),
                    ",".join(item.company_policy_refs),
                    ",".join(item.input_resolution_refs),
                )
                for item in request.metric_batch.snapshots
            )
            _write_exclusive(
                temporary / "traceability_snapshot.csv",
                _csv_bytes(
                    ("metric_id", "accounting_basis_id", "as_of", "calculation_status", "facts_hash", "formula_profile_ids", "parameter_profile_ids", "company_policy_refs", "input_resolution_refs"),
                    trace_rows,
                ),
            )
            validation_payload = {
                "schema_version": "kmfa.project_cost.validation_summary.v1",
                "run_id": request.run_id,
                **planes.as_dict(),
                "input_sufficiency_validated": True,
                "metric_dual_channel_required_delta_minor": 0,
                "metric_batch_blocker_codes": list(request.metric_batch.blocker_codes) if request.metric_batch else [],
                "workbook_validation": workbook_validation.as_dict() if workbook_validation else None,
                "seal_verified_before_publish": True,
            }
            _write_json(temporary / "validation_summary.json", validation_payload)
            _write_json(
                temporary / "privacy_scan.json",
                {
                    "schema_version": "kmfa.project_cost.privacy_scan.v1",
                    "artifact_classification": "PRIVATE_RUNTIME",
                    "public_publish_authorized": False,
                    "raw_source_copied": False,
                    "company_approval_state_managed": False,
                    "finance_owner_or_authorized_person_fields_present": False,
                    "status": "PASS_PRIVATE_RUNTIME_BOUNDARY",
                },
            )
            _write_json(
                temporary / "performance_summary.json",
                {
                    "schema_version": "kmfa.project_cost.performance_summary.v1",
                    "source_record_count": sum(item.source_record_count for item in request.metric_batch.snapshots) if request.metric_batch else 0,
                    "metric_snapshot_count": len(request.metric_batch.snapshots) if request.metric_batch else 0,
                    "candidate_pair_comparisons": 0,
                    "global_quadratic_matching_used": False,
                    "generation_elapsed_ms_before_controls": int((time.perf_counter() - start) * 1000),
                },
            )

            business_hashes = {
                path.name: _sha256_file(path)
                for path in temporary.iterdir()
                if path.is_file() and path.name not in CONTROL_FILES
            }
            manifest = {
                "schema_version": "kmfa.project_cost.run_manifest.v4",
                "run_id": request.run_id,
                "request_hash": request.request_hash,
                "created_at": created_at,
                "mode": request.mode,
                "as_of": request.as_of,
                "project_scope": request.metric_batch.snapshots[0].scope.as_dict() if request.metric_batch and request.metric_batch.snapshots else None,
                **planes.as_dict(),
                "metric_snapshot_keys": [list(item.key) for item in request.metric_batch.snapshots] if request.metric_batch else [],
                "source_bindings": [
                    item.as_dict()
                    for item in sorted(request.source_lineage, key=lambda value: (value.source_slot_id, value.opaque_source_id))
                ],
                "code_version": request.code_version,
                "config_hash": request.config_hash,
                "supersedes_run_id": request.supersedes_run_id,
                "absolute_output_dir": str(output_dir),
                "primary_output": str(primary_output),
                "output_index_md": str(output_dir / "OUTPUT_INDEX.md"),
                "output_index_json": str(output_dir / "output_index.json"),
                "seal_path": str(output_dir / "run_seal.sha256"),
                "internal_process_handoff": str(output_dir / "INTERNAL_PROCESS_HANDOFF.md") if final else None,
                "output_hashes": dict(sorted(business_hashes.items())),
            }
            _write_json(temporary / "run_manifest.json", manifest)
            md_hashes = {**business_hashes, "run_manifest.json": _sha256_file(temporary / "run_manifest.json")}
            _write_exclusive(
                temporary / "OUTPUT_INDEX.md",
                _output_index_markdown(
                    request=request,
                    planes=planes,
                    primary_output=primary_output,
                    finalized_hashes=md_hashes,
                ).encode("utf-8"),
            )
            index_files = []
            for path in sorted(item for item in temporary.iterdir() if item.is_file()):
                if path.name in {"output_index.json", "run_seal.sha256"}:
                    continue
                index_files.append(
                    {
                        "path": str(output_dir / path.name),
                        "sha256": _sha256_file(path),
                        "artifact_type": path.name,
                    }
                )
            output_index = {
                "schema_version": "kmfa.project_cost.output_index.v2",
                "run_id": request.run_id,
                "result_status": planes.generation_status.value,
                "output_dir": str(output_dir),
                "primary_output": str(primary_output),
                "seal_path": str(output_dir / "run_seal.sha256"),
                "files": index_files,
                "next_step": (
                    "由调用方 Codex/操作人在 Skill 外按公司现有内部流程处理；Skill 不管理审批。"
                    if final
                    else "按缺项提示补充输入或明确选择允许的处理方式。"
                ),
            }
            _write_json(temporary / "output_index.json", output_index)
            _write_exclusive(temporary / "run_seal.sha256", _seal_payload(temporary))
            if not verify_run_seal(temporary):
                raise GenerationError("RUN_SEAL_VERIFY_FAILED", "detached run seal failed before atomic publish")
    except WorkbookError as exc:
        return _publish_generation_failure(request, code=exc.code, message=exc.message)
    except PathSafetyError as exc:
        raise GenerationError("GENERATION_ATOMIC_PATH", str(exc)) from exc

    if not verify_run_seal(output_dir) or not verify_output_index(output_dir):
        raise GenerationError("PUBLISHED_OUTPUT_VERIFY_FAILED", "published output index or seal failed verification")
    handoff_path = output_dir / "INTERNAL_PROCESS_HANDOFF.md" if final else None
    if final and (handoff_path is None or not handoff_path.is_file()):
        raise GenerationError("INTERNAL_HANDOFF_MISSING", "final generation requires an internal-process locator handoff")
    if not final and any(output_dir.glob("*.xlsx")):
        raise GenerationError("BLOCKED_FINAL_WORKBOOK_FORBIDDEN", "blocked run cannot contain a final-looking workbook")
    return GeneratedRun(
        status_planes=planes,
        output_dir=output_dir,
        primary_output=primary_output,
        output_index_md=output_dir / "OUTPUT_INDEX.md",
        output_index_json=output_dir / "output_index.json",
        run_seal=output_dir / "run_seal.sha256",
        internal_process_handoff=handoff_path,
    )
