"""Safe values-only project-cost workbook creation through the bundled artifact runtime."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET

from .security import SecurityProfile, escape_spreadsheet_text, require_safe_ooxml


EXPECTED_SHEETS = (
    "01_项目成本表",
    "02_成本明细",
    "03_生命周期对照",
    "04_收入与现金",
    "05_来源与核销",
    "06_差异与待确认",
    "07_项目身份",
    "08_运行说明",
)
FORMULA_ERROR_TOKENS = (b"#REF!", b"#DIV/0!", b"#VALUE!", b"#NAME?", b"#N/A")


class WorkbookError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class ArtifactToolRuntime:
    node_executable: Path
    node_modules_dir: Path

    def validate(self) -> None:
        node = Path(self.node_executable)
        modules = Path(self.node_modules_dir)
        try:
            node_stat = node.lstat()
            modules_stat = modules.lstat()
        except OSError as exc:
            raise WorkbookError("WORKBOOK_RUNTIME_MISSING", "bundled Node runtime is unavailable") from exc
        if not stat.S_ISREG(node_stat.st_mode) or not os.access(node, os.X_OK):
            raise WorkbookError("WORKBOOK_NODE_INVALID", "bundled Node executable is not an executable file")
        if not stat.S_ISDIR(modules_stat.st_mode) or modules.is_symlink():
            raise WorkbookError("WORKBOOK_MODULES_INVALID", "bundled node_modules must be a real directory")
        if not (modules / "@oai" / "artifact-tool").is_dir():
            raise WorkbookError("WORKBOOK_ARTIFACT_TOOL_MISSING", "@oai/artifact-tool is unavailable")

    @classmethod
    def from_environment(cls, environment: Optional[Mapping[str, str]] = None) -> "ArtifactToolRuntime":
        values = dict(os.environ if environment is None else environment)
        node = values.get("CODEX_SPREADSHEET_NODE")
        modules = values.get("CODEX_SPREADSHEET_NODE_MODULES")
        if not node or not modules:
            raise WorkbookError(
                "WORKBOOK_RUNTIME_INPUT_REQUIRED",
                "load_workspace_dependencies must provide CODEX_SPREADSHEET_NODE and CODEX_SPREADSHEET_NODE_MODULES",
            )
        runtime = cls(Path(node), Path(modules))
        runtime.validate()
        return runtime


@dataclass(frozen=True)
class WorkbookSheet:
    name: str
    title: str
    headers: Tuple[str, ...]
    rows: Tuple[Tuple[Any, ...], ...]
    column_kinds: Tuple[str, ...]
    column_widths: Tuple[int, ...]

    def as_payload(self) -> Dict[str, Any]:
        if self.name not in EXPECTED_SHEETS:
            raise WorkbookError("WORKBOOK_SHEET_UNKNOWN", "sheet name is outside the R9 contract")
        if not self.title or not self.headers or len(self.headers) != len(self.column_kinds):
            raise WorkbookError("WORKBOOK_SHEET_INVALID", "sheet title, headers, and kinds are required")
        if self.column_widths and len(self.column_widths) != len(self.headers):
            raise WorkbookError("WORKBOOK_WIDTHS_INVALID", "column widths must match the header count")
        safe_rows = []
        for row in self.rows:
            if len(row) != len(self.headers):
                raise WorkbookError("WORKBOOK_ROW_WIDTH_INVALID", "row width differs from the sheet header")
            safe_rows.append([sanitize_cell_value(value) for value in row])
        return {
            "name": self.name,
            "title": escape_spreadsheet_text(self.title),
            "headers": [escape_spreadsheet_text(value) for value in self.headers],
            "rows": safe_rows,
            "column_kinds": list(self.column_kinds),
            "column_widths": list(self.column_widths),
        }


@dataclass(frozen=True)
class WorkbookValidation:
    workbook_sha256: str
    semantic_workbook_sha256: str
    sheet_names: Tuple[str, ...]
    formula_cell_count: int
    external_relationship_count: int
    active_content_count: int
    formula_error_token_count: int
    style_cell_format_count: int
    preview_sha256: Tuple[Tuple[str, str], ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "workbook_sha256": self.workbook_sha256,
            "semantic_workbook_sha256": self.semantic_workbook_sha256,
            "sheet_names": list(self.sheet_names),
            "formula_cell_count": self.formula_cell_count,
            "external_relationship_count": self.external_relationship_count,
            "active_content_count": self.active_content_count,
            "formula_error_token_count": self.formula_error_token_count,
            "style_cell_format_count": self.style_cell_format_count,
            "preview_sha256": [dict(file=name, sha256=digest) for name, digest in self.preview_sha256],
            "visual_render_status": "PASS_ALL_SHEETS",
        }


def sanitize_cell_value(value: Any) -> Any:
    if value is None or isinstance(value, bool) or (isinstance(value, int) and not isinstance(value, bool)):
        return value
    if isinstance(value, str):
        return escape_spreadsheet_text(value)
    if isinstance(value, float):
        raise WorkbookError("WORKBOOK_FLOAT_FORBIDDEN", "money and workbook values cannot use a float path")
    raise WorkbookError("WORKBOOK_VALUE_TYPE_INVALID", "workbook values must be text, integer, boolean, or null")


def minor_to_cny_display(value: Optional[int]) -> str:
    if value is None:
        return ""
    if isinstance(value, bool) or not isinstance(value, int):
        raise WorkbookError("WORKBOOK_MONEY_INVALID", "display money must originate from integer minor units")
    sign = "-" if value < 0 else ""
    absolute = abs(value)
    return "%s%d.%02d" % (sign, absolute // 100, absolute % 100)


def _write_exclusive(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _semantic_workbook_hash(path: Path) -> str:
    digest = hashlib.sha256()
    ignored = {"docProps/core.xml", "docProps/app.xml", "xl/calcChain.xml"}
    with zipfile.ZipFile(path) as archive:
        for name in sorted(item for item in archive.namelist() if item not in ignored):
            data = archive.read(name)
            if name.endswith((".xml", ".rels")):
                try:
                    data = ET.tostring(ET.fromstring(data), encoding="utf-8")
                except ET.ParseError as exc:
                    raise WorkbookError("WORKBOOK_XML_INVALID", "generated workbook contains malformed XML") from exc
            digest.update(name.encode("utf-8"))
            digest.update(b"\x00")
            digest.update(data)
            digest.update(b"\x00")
    return digest.hexdigest()


def _sheet_names(path: Path) -> Tuple[str, ...]:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("xl/workbook.xml"))
    names = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] == "sheet":
            if node.attrib.get("state", "visible") != "visible":
                raise WorkbookError("WORKBOOK_HIDDEN_SHEET", "all output sheets must remain visible")
            names.append(node.attrib.get("name", ""))
    return tuple(names)


def _style_count(path: Path) -> int:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("xl/styles.xml"))
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] == "cellXfs":
            return int(node.attrib.get("count", "0"))
    return 0


def validate_generated_workbook(
    workbook_path: Path,
    *,
    security_profile: SecurityProfile,
    preview_files: Sequence[Path],
) -> WorkbookValidation:
    workbook_path = Path(workbook_path)
    report = require_safe_ooxml(workbook_path.parent, workbook_path, profile=security_profile)
    names = _sheet_names(workbook_path)
    if names != EXPECTED_SHEETS:
        raise WorkbookError("WORKBOOK_SHEET_CONTRACT", "generated workbook sheet order or names drifted")
    if len(preview_files) != len(EXPECTED_SHEETS):
        raise WorkbookError("WORKBOOK_VISUAL_RENDER_INCOMPLETE", "every sheet requires one visual render")
    preview_hashes = []
    for preview in preview_files:
        value = Path(preview)
        if not value.is_file() or value.stat().st_size < 128:
            raise WorkbookError("WORKBOOK_VISUAL_RENDER_INVALID", "sheet preview is missing or empty")
        preview_hashes.append((value.name, _sha256_file(value)))
    error_count = 0
    active_count = 0
    external_count = 0
    with zipfile.ZipFile(workbook_path) as archive:
        for name in archive.namelist():
            lowered = name.casefold()
            if any(token in lowered for token in ("vbaproject", "activex", "embeddings", "externallinks", "connections")):
                active_count += 1
            data = archive.read(name)
            error_count += sum(data.count(token) for token in FORMULA_ERROR_TOKENS)
            if name.endswith(".rels") and b'TargetMode="External"' in data:
                external_count += 1
    if active_count or external_count or error_count or report.formula_cell_count or report.dde_formula_count:
        raise WorkbookError("WORKBOOK_ACTIVE_OR_FORMULA_CONTENT", "generated workbook must be values-only and self-contained")
    style_count = _style_count(workbook_path)
    if style_count < 3:
        raise WorkbookError("WORKBOOK_STYLES_MISSING", "generated workbook lacks the required visual hierarchy")
    return WorkbookValidation(
        workbook_sha256=_sha256_file(workbook_path),
        semantic_workbook_sha256=_semantic_workbook_hash(workbook_path),
        sheet_names=names,
        formula_cell_count=report.formula_cell_count,
        external_relationship_count=external_count,
        active_content_count=active_count,
        formula_error_token_count=error_count,
        style_cell_format_count=style_count,
        preview_sha256=tuple(preview_hashes),
    )


def build_project_cost_workbook(
    *,
    sheets: Sequence[WorkbookSheet],
    output_path: Path,
    work_directory: Path,
    runtime: ArtifactToolRuntime,
    security_profile: SecurityProfile,
    timeout_seconds: int = 120,
    visual_evidence_dir: Optional[Path] = None,
) -> WorkbookValidation:
    """Build, visually render, export, and structurally validate one final workbook."""

    runtime.validate()
    ordered = tuple(sheets)
    if tuple(item.name for item in ordered) != EXPECTED_SHEETS:
        raise WorkbookError("WORKBOOK_SHEET_CONTRACT", "workbook requires the eight registered sheets in order")
    output_path = Path(output_path)
    work_directory = Path(work_directory)
    if output_path.exists() or work_directory.exists():
        raise WorkbookError("WORKBOOK_TARGET_EXISTS", "workbook and scratch targets must be new")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    work_directory.mkdir(parents=False, exist_ok=False)
    node_modules_link = work_directory / "node_modules"
    node_modules_link.symlink_to(runtime.node_modules_dir, target_is_directory=True)
    payload_path = work_directory / "workbook_payload.json"
    preview_dir = work_directory / "previews"
    payload = {
        "schema_version": "kmfa.project_cost.workbook_payload.v1",
        "sheets": [item.as_payload() for item in ordered],
    }
    _write_exclusive(
        payload_path,
        (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    builder = Path(__file__).resolve().parents[2] / "scripts" / "build_project_cost_workbook.mjs"
    if not builder.is_file() or builder.is_symlink():
        raise WorkbookError("WORKBOOK_BUILDER_MISSING", "the registered workbook builder is unavailable")
    runtime_builder = work_directory / builder.name
    shutil.copyfile(builder, runtime_builder)
    try:
        completed = subprocess.run(
            [str(runtime.node_executable), str(runtime_builder), str(payload_path), str(output_path), str(preview_dir)],
            cwd=work_directory,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env={**os.environ, "NO_COLOR": "1"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WorkbookError("WORKBOOK_BUILD_EXECUTION", "artifact-tool workbook build could not complete") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "unknown artifact-tool failure").strip()[-2000:]
        raise WorkbookError("WORKBOOK_BUILD_FAILED", detail)
    try:
        result = json.loads(completed.stdout.strip().splitlines()[-1])
        previews = tuple(Path(value) for value in result["preview_files"])
    except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise WorkbookError("WORKBOOK_BUILD_RESULT_INVALID", "artifact-tool result metadata is invalid") from exc
    validation = validate_generated_workbook(
        output_path,
        security_profile=security_profile,
        preview_files=previews,
    )
    if visual_evidence_dir is not None:
        evidence = Path(visual_evidence_dir)
        if not evidence.is_absolute() or evidence.exists() or not evidence.parent.is_dir():
            raise WorkbookError(
                "WORKBOOK_VISUAL_EVIDENCE_PATH_INVALID",
                "visual evidence directory must be a new absolute path with an existing parent",
            )
        evidence.mkdir()
        for index, preview in enumerate(previews, 1):
            shutil.copyfile(preview, evidence / ("%02d.png" % index))
    shutil.rmtree(work_directory)
    return validation
