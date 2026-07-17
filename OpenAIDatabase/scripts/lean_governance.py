#!/usr/bin/env python3
"""Project-local governance renderer and fail-closed validator.

The repository split retired the multi-project CodexProject governance CLI.
This replacement owns only OpenAIDatabase.  It reads the current canonical
governance files and deterministically renders the three owner-facing views;
it does not restore the retired root governance registry or a second fact
source.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


CANONICAL_FILES = (
    "docs/governance/project.yaml",
    "docs/governance/roadmap.yaml",
    "docs/governance/events.jsonl",
    "VERSION",
    "CHANGELOG.md",
)
VIEW_NAMES = ("功能清单.md", "开发记录.md", "模型参数文件.md")
GENERATED = "<!-- 由 OpenAIDatabase/scripts/lean_governance.py 从当前 canonical governance 生成；请勿手写。 -->"


class GovernanceError(ValueError):
    """Stable validation error."""


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(line):
        if char == "\\" and not escaped:
            escaped = True
            continue
        if char == "'" and not in_double and not escaped:
            in_single = not in_single
        elif char == '"' and not in_single and not escaped:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:index].rstrip()
        escaped = False
    return line.rstrip()


def _split_inline(text: str) -> list[str]:
    values: list[str] = []
    start = 0
    in_single = False
    in_double = False
    escaped = False
    depth = 0
    for index, char in enumerate(text):
        if char == "\\" and in_double and not escaped:
            escaped = True
            continue
        if char == "'" and not in_double and not escaped:
            in_single = not in_single
        elif char == '"' and not in_single and not escaped:
            in_double = not in_double
        elif not in_single and not in_double:
            if char in "[{(":
                depth += 1
            elif char in "]})":
                depth = max(0, depth - 1)
            elif char == "," and depth == 0:
                values.append(text[start:index])
                start = index + 1
        escaped = False
    values.append(text[start:])
    return values


def _scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [] if not inner else [_scalar(part) for part in _split_inline(inner)]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def _split_key_value(text: str) -> tuple[str, str | None]:
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(text):
        if char == "\\" and not escaped:
            escaped = True
            continue
        if char == "'" and not in_double and not escaped:
            in_single = not in_single
        elif char == '"' and not in_single and not escaped:
            in_double = not in_double
        elif char == ":" and not in_single and not in_double:
            return text[:index].strip(), text[index + 1 :].strip()
        escaped = False
    return text.strip(), None


def load_yaml(path: Path) -> Any:
    """Load the repository's JSON-compatible YAML subset without dependencies."""

    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        cleaned = _strip_comment(raw)
        if cleaned.strip():
            lines.append((len(cleaned) - len(cleaned.lstrip(" ")), cleaned.strip()))
    if not lines:
        return {}

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if lines[index][1] == "-" or lines[index][1].startswith("- "):
            result: list[Any] = []
            while index < len(lines) and lines[index][0] == indent and (
                lines[index][1] == "-" or lines[index][1].startswith("- ")
            ):
                item_text = lines[index][1][1:].strip()
                index += 1
                if not item_text:
                    item, index = parse_block(index, lines[index][0])
                    result.append(item)
                    continue
                key, value = _split_key_value(item_text)
                if value is None:
                    result.append(_scalar(item_text))
                    continue
                item_map: dict[str, Any] = {key: _scalar(value) if value else {}}
                while index < len(lines) and lines[index][0] > indent:
                    child_indent, child_text = lines[index]
                    child_key, child_value = _split_key_value(child_text)
                    if child_value is None:
                        break
                    if child_value:
                        item_map[child_key] = _scalar(child_value)
                        index += 1
                    elif index + 1 < len(lines) and lines[index + 1][0] > child_indent:
                        child, index = parse_block(index + 1, lines[index + 1][0])
                        item_map[child_key] = child
                    else:
                        item_map[child_key] = {}
                        index += 1
                result.append(item_map)
            return result, index

        result_map: dict[str, Any] = {}
        while index < len(lines) and lines[index][0] == indent and not (
            lines[index][1] == "-" or lines[index][1].startswith("- ")
        ):
            key, value = _split_key_value(lines[index][1])
            if value is None:
                raise GovernanceError(f"invalid_yaml_line:{lines[index][1]}")
            if value:
                result_map[key] = _scalar(value)
                index += 1
            elif index + 1 < len(lines) and lines[index + 1][0] > indent:
                child, index = parse_block(index + 1, lines[index + 1][0])
                result_map[key] = child
            else:
                result_map[key] = {}
                index += 1
        return result_map, index

    parsed, end = parse_block(0, lines[0][0])
    if end != len(lines):
        raise GovernanceError(f"yaml_parse_incomplete:{lines[end][1]}")
    return parsed


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GovernanceError(f"invalid_jsonl:{path.name}:{line_number}") from exc
        if not isinstance(value, dict):
            raise GovernanceError(f"invalid_jsonl_shape:{path.name}:{line_number}")
        rows.append(value)
    return rows


def _cell(value: Any) -> str:
    if value is None or value == "":
        return "NOT_APPLICABLE"
    if isinstance(value, list):
        return ", ".join(_cell(item) for item in value) or "NOT_APPLICABLE"
    text = str(value).replace("|", "\\|").replace("\n", " ")
    return text


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "> 当前 canonical facts 中没有对应记录。"
    output = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    output.extend("| " + " | ".join(_cell(value) for value in row) + " |" for row in rows)
    return "\n".join(output)


def _roadmap_rows(roadmap: dict[str, Any]) -> tuple[list[list[Any]], list[list[Any]]]:
    phase_rows: list[list[Any]] = []
    task_rows: list[list[Any]] = []
    for stage in roadmap.get("stages", []):
        if not isinstance(stage, dict):
            continue
        stage_id = stage.get("stage_id")
        for phase in stage.get("phases", []):
            if not isinstance(phase, dict):
                continue
            phase_rows.append(
                [
                    stage_id,
                    phase.get("phase_id"),
                    phase.get("name"),
                    phase.get("status"),
                    (phase.get("stop_gate") or {}).get("gate_id")
                    if isinstance(phase.get("stop_gate"), dict)
                    else None,
                ]
            )
            for task in phase.get("tasks", []):
                if isinstance(task, dict):
                    task_rows.append(
                        [
                            phase.get("phase_id"),
                            task.get("task_id"),
                            task.get("name"),
                            task.get("status"),
                            task.get("acceptance_ids"),
                        ]
                    )
    return phase_rows, task_rows


def build_views(database_dir: Path) -> dict[str, str]:
    governance = database_dir / "docs/governance"
    project = load_yaml(governance / "project.yaml")
    roadmap = load_yaml(governance / "roadmap.yaml")
    models = load_yaml(governance / "model_registry.yaml")
    formulas = load_yaml(governance / "formula_registry.yaml")
    events = _load_jsonl(governance / "events.jsonl")
    development_events = _load_jsonl(governance / "development_events.jsonl")
    if not all(isinstance(value, dict) for value in (project, roadmap, models, formulas)):
        raise GovernanceError("canonical_governance_shape_invalid")
    phase_rows, task_rows = _roadmap_rows(roadmap)

    feature_rows = [
        [
            row.get("feature_id") or row.get("id"),
            row.get("name"),
            row.get("status"),
            row.get("description") or row.get("objective"),
            row.get("fact_level"),
        ]
        for row in project.get("features", [])
        if isinstance(row, dict)
    ]
    feature_text = "\n".join(
        [
            GENERATED,
            "# 功能清单",
            "",
            "## 摘要",
            "",
            f"- project_id: `{_cell(project.get('project_id'))}`",
            f"- version: `{_cell(project.get('version'))}`",
            f"- current_status: `{_cell(project.get('current_status'))}`",
            f"- current_stage: `{_cell(roadmap.get('current_stage_id'))}`",
            f"- current_task: `{_cell(roadmap.get('current_task_id'))}`",
            f"- delivery_readiness: `{_cell(project.get('delivery_readiness'))}`",
            f"- evidence_status: `{_cell(project.get('fact_level'))}`",
            "",
            "## 功能",
            "",
            _table(["编号", "功能", "状态", "说明", "事实等级"], feature_rows),
            "",
            "## 已知限制",
            "",
            *[f"- {_cell(item)}" for item in project.get("limitations", [])],
            "",
        ]
    )

    recent_events = (events + development_events)[-24:]
    event_rows = [
        [
            row.get("event_id") or row.get("id"),
            row.get("timestamp") or row.get("occurred_at") or row.get("date"),
            row.get("task_id"),
            row.get("status") or row.get("result"),
            row.get("summary") or row.get("description") or row.get("event"),
        ]
        for row in recent_events
    ]
    development_text = "\n".join(
        [
            GENERATED,
            "# 开发记录",
            "",
            "## 摘要",
            "",
            f"- current_stage: `{_cell(roadmap.get('current_stage_id'))}`",
            f"- current_phase: `{_cell(roadmap.get('current_phase_id'))}`",
            f"- current_task: `{_cell(roadmap.get('current_task_id'))}`",
            f"- next_gate: `{_cell(roadmap.get('next_gate_id'))}`",
            f"- canonical_event_count: `{len(events)}`",
            f"- development_event_count: `{len(development_events)}`",
            "",
            "## Stage -> Phase -> Task",
            "",
            _table(["Stage", "Phase", "名称", "状态", "stop_gate"], phase_rows),
            "",
            _table(["Phase", "Task", "名称", "状态", "acceptance"], task_rows),
            "",
            "## 最近事件",
            "",
            _table(["事件", "时间", "Task", "状态", "摘要"], event_rows),
            "",
        ]
    )

    with (governance / "parameter_registry.csv").open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        parameter_rows = list(csv.DictReader(handle))
    model_rows = [
        [
            row.get("model_id"),
            row.get("name"),
            row.get("status"),
            row.get("fact_level"),
            row.get("implementation_ref") or row.get("code_ref"),
        ]
        for row in models.get("models", [])
        if isinstance(row, dict)
    ]
    formula_rows = [
        [
            row.get("formula_id"),
            row.get("name"),
            row.get("expression") or row.get("formula"),
            row.get("status"),
            row.get("fact_level"),
        ]
        for row in formulas.get("formulas", [])
        if isinstance(row, dict)
    ]
    parameter_view_rows = [
        [
            row.get("parameter_id"),
            row.get("model_id"),
            row.get("symbol"),
            row.get("active_value"),
            row.get("unit"),
            row.get("status"),
            row.get("semantic_status"),
        ]
        for row in parameter_rows
    ]
    model_text = "\n".join(
        [
            GENERATED,
            "# 模型参数文件",
            "",
            "## 摘要",
            "",
            f"- active_model_count: `{sum(row[2] == 'active' for row in model_rows)}`",
            f"- active_formula_count: `{sum(row[3] == 'active' for row in formula_rows)}`",
            f"- active_parameter_count: `{sum(row.get('status') == 'active' for row in parameter_rows)}`",
            f"- total_parameter_count: `{len(parameter_rows)}`",
            "",
            "## 模型",
            "",
            _table(["模型", "名称", "状态", "事实等级", "实现"], model_rows),
            "",
            "## 公式",
            "",
            _table(["公式", "名称", "表达式", "状态", "事实等级"], formula_rows),
            "",
            "## 参数",
            "",
            _table(
                ["参数", "模型", "符号", "当前值", "单位", "状态", "语义状态"],
                parameter_view_rows,
            ),
            "",
        ]
    )
    return {
        "功能清单.md": feature_text,
        "开发记录.md": development_text,
        "模型参数文件.md": model_text,
    }


def _validate(database_dir: Path, *, enforce_sync: bool) -> dict[str, Any]:
    errors: list[str] = []
    for relative in CANONICAL_FILES:
        path = database_dir / relative
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"canonical_file_missing:{relative}")
    try:
        project = load_yaml(database_dir / "docs/governance/project.yaml")
        roadmap = load_yaml(database_dir / "docs/governance/roadmap.yaml")
        if project.get("project_id") != "OpenAIDatabase":
            errors.append("project_id_invalid")
        if roadmap.get("project_id") != "OpenAIDatabase":
            errors.append("roadmap_project_id_invalid")
        if roadmap.get("roadmap_kind") != "product":
            errors.append("roadmap_kind_invalid")
        views = build_views(database_dir)
        if enforce_sync:
            for name, expected in views.items():
                path = database_dir / name
                if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                    errors.append(f"generated_view_drift:{name}")
    except (OSError, GovernanceError, AttributeError, csv.Error) as exc:
        errors.append(str(exc))
    return {
        "schema_version": "openai_database.local_governance_validation.v1",
        "status": "PASS" if not errors else "FAIL_CLOSED",
        "project_id": "OpenAIDatabase",
        "errors": errors,
        "warnings": [],
    }


def _changed(database_dir: Path, base_ref: str) -> bool:
    root = database_dir.parent
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD", "--", "OpenAIDatabase"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise GovernanceError("changed_scope_git_diff_failed")
    worktree = subprocess.run(
        ["git", "status", "--short", "--", "OpenAIDatabase"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if worktree.returncode != 0:
        raise GovernanceError("changed_scope_git_status_failed")
    return bool(result.stdout.strip() or worktree.stdout.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("render")
    render.add_argument("--write", action="store_true")
    sub.add_parser("check-render")
    validate = sub.add_parser("validate")
    validate.add_argument("--changed-only", action="store_true")
    validate.add_argument("--enforce-sync", action="store_true")
    validate.add_argument("--semantic", action="store_true")
    validate.add_argument("--base-ref", default="origin/main")
    ci = sub.add_parser("ci")
    ci.add_argument("--changed-only", action="store_true")
    ci.add_argument("--base-ref", default="origin/main")
    args = parser.parse_args(argv)
    database_dir = args.database_dir.expanduser().resolve(strict=True)

    if args.command == "render":
        views = build_views(database_dir)
        if args.write:
            for name, text in views.items():
                (database_dir / name).write_text(text, encoding="utf-8")
        print(json.dumps({"status": "PASS", "views": sorted(views), "written": args.write}, ensure_ascii=False))
        return 0
    if args.command == "check-render":
        report = _validate(database_dir, enforce_sync=True)
    else:
        if args.changed_only and not _changed(database_dir, args.base_ref):
            report = {
                "schema_version": "openai_database.local_governance_validation.v1",
                "status": "PASS",
                "project_id": "OpenAIDatabase",
                "errors": [],
                "warnings": [],
                "changed_scope": False,
            }
        else:
            report = _validate(
                database_dir,
                enforce_sync=args.command == "ci" or bool(getattr(args, "enforce_sync", False)),
            )
            report["changed_scope"] = True
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
