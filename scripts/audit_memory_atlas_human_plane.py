#!/usr/bin/env python3
"""Audit the bounded, owner-readable Memory Atlas document plane."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


EXPECTED_FILES = {
    "快速开始.md",
    "系统使用.md",
    "功能工作流.md",
    "同步备份.md",
    "模型参数.md",
    "版本路线图.md",
    "维护故障.md",
}
OWNER_ENTRY_CONTRACT = Path("config/memory_atlas_owner_entries.json")
OWNER_ENTRY_SCHEMA = "memory_atlas.owner_entries.v1_2_1_s05_p1_t2"
OWNER_ENTRY_LIMITS = {
    "max_reading_minutes": 2,
    "max_bytes_per_file": 6000,
    "max_lines_per_file": 80,
    "status_heading_max_line": 4,
    "next_heading_max_line": 18,
    "status_and_next_max_chars": 1500,
}
OWNER_ENTRY_REQUIRED_STATUS_TOKENS = {"Task Pack 进度", "当前 Task", "未发布"}
OWNER_ENTRY_REQUIRED_NEXT_TOKENS = {"下一 Task"}
OWNER_ENTRY_REQUIRED_SECTIONS = {
    "功能清单.md": {"## 当前状态", "## 下一步", "## 核心功能", "## 使用与边界"},
    "开发记录.md": {"## 当前状态", "## 下一步", "## 最近完成", "## 验证与恢复"},
    "模型参数文件.md": {"## 当前状态", "## 下一步", "## 模型总览", "## 关键参数", "## 模型边界"},
}
OWNER_ENTRY_FORBIDDEN_SECTIONS = {
    "功能清单.md": {"## 证据"},
    "开发记录.md": {"## Roadmap", "## 近期事件"},
    "模型参数文件.md": {"## 公式", "## 参数"},
}
CHANGE_USAGE_MAP_CONTRACT = Path("config/memory_atlas_change_usage_map.json")
CHANGE_USAGE_MAP_SCHEMA = "memory_atlas.change_usage_map.v1_2_1_s05_p1_t3"
CHANGE_USAGE_MAP_FILE = "版本路线图.md"
CHANGE_USAGE_MAP_LIMITS = {"max_lines": 160, "max_bytes": 12000}
CHANGE_CATEGORY_NAMES = ("新增", "修改", "删除或隐藏")
CORE_WORKFLOW_NAMES = ("建议与行动", "资产与主题", "编辑与提案", "复盘与迭代", "同步与备份")
CHANGE_USAGE_MAP_REQUIRED_SECTIONS = {
    "## 结论",
    "## 操作",
    "## 本次交付改变了什么",
    "## 五个核心用户流程",
    "## 尚未交付",
    "## 后续路线",
    "## 交付规则",
}
MOJIBAKE_MARKERS = ("\ufffd", "锟斤拷", "烫烫烫", "屯屯屯")
INLINE_LINK_RE = re.compile(
    r"!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)
REFERENCE_DEFINITION_RE = re.compile(r"(?m)^[ \t]{0,3}\[([^\]\n]+)\]:[ \t]*(<[^>\n]+>|\S+)")
REFERENCE_USE_RE = re.compile(r"!?\[([^\]\n]+)\](?:\[([^\]\n]*)\])?")
CHINESE_RE = re.compile(r"[\u3400-\u9fff]")


def section_body(lines: list[str], heading: str) -> str:
    try:
        start = lines.index(heading) + 1
    except ValueError:
        return ""
    end = next((index for index in range(start, len(lines)) if lines[index].startswith("## ")), len(lines))
    return "\n".join(lines[start:end]).strip()


def audit_owner_entries(database_dir: Path) -> tuple[list[dict[str, object]], list[str]]:
    contract_path = database_dir / OWNER_ENTRY_CONTRACT
    if not contract_path.is_file():
        return [], [f"缺少 owner 入口合同：{OWNER_ENTRY_CONTRACT.as_posix()}"]
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [], [f"owner 入口合同无法解析：{exc}"]
    if contract.get("schema_version") != OWNER_ENTRY_SCHEMA:
        return [], [f"owner 入口合同 schema 不匹配：{contract.get('schema_version')}"]

    file_contracts = contract.get("files")
    if not isinstance(file_contracts, dict) or set(file_contracts) != set(OWNER_ENTRY_REQUIRED_SECTIONS):
        return [], ["owner 入口合同必须精确定义三件套"]

    contract_errors: list[str] = []
    for field, expected in OWNER_ENTRY_LIMITS.items():
        if contract.get(field) != expected:
            contract_errors.append(f"owner 入口合同不得放宽 {field}：必须为 {expected}")
    if set(contract.get("required_status_tokens", [])) != OWNER_ENTRY_REQUIRED_STATUS_TOKENS:
        contract_errors.append("owner 入口合同 required_status_tokens 不得变更")
    if set(contract.get("required_next_tokens", [])) != OWNER_ENTRY_REQUIRED_NEXT_TOKENS:
        contract_errors.append("owner 入口合同 required_next_tokens 不得变更")
    for filename, raw_file_contract in file_contracts.items():
        file_contract = raw_file_contract if isinstance(raw_file_contract, dict) else {}
        if set(file_contract.get("required_sections", [])) != OWNER_ENTRY_REQUIRED_SECTIONS[filename]:
            contract_errors.append(f"owner 入口合同不得放宽 {filename} required_sections")
        if set(file_contract.get("forbidden_exact_sections", [])) != OWNER_ENTRY_FORBIDDEN_SECTIONS[filename]:
            contract_errors.append(f"owner 入口合同不得变更 {filename} forbidden_exact_sections")
    key_parameter_ids = [str(item) for item in contract.get("key_parameter_ids", [])]
    if len(key_parameter_ids) < 8 or len(key_parameter_ids) != len(set(key_parameter_ids)):
        contract_errors.append("owner 入口合同必须保留至少 8 个不重复关键参数")
    if contract_errors:
        return [], contract_errors

    max_bytes = int(contract.get("max_bytes_per_file") or 0)
    max_lines = int(contract.get("max_lines_per_file") or 0)
    status_max_line = int(contract.get("status_heading_max_line") or 0)
    next_max_line = int(contract.get("next_heading_max_line") or 0)
    status_next_max_chars = int(contract.get("status_and_next_max_chars") or 0)
    required_status_tokens = [str(item) for item in contract.get("required_status_tokens", [])]
    required_next_tokens = [str(item) for item in contract.get("required_next_tokens", [])]
    errors: list[str] = []
    reports: list[dict[str, object]] = []

    for filename, raw_file_contract in file_contracts.items():
        path = database_dir / filename
        if not path.is_file():
            errors.append(f"缺少 owner 入口：{filename}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{filename} 不是有效 UTF-8：{exc}")
            continue
        lines = text.splitlines()
        size_bytes = len(text.encode("utf-8"))
        line_count = len(lines)
        file_contract = raw_file_contract if isinstance(raw_file_contract, dict) else {}
        required_sections = [str(item) for item in file_contract.get("required_sections", [])]
        forbidden_sections = [str(item) for item in file_contract.get("forbidden_exact_sections", [])]

        for section in required_sections:
            if section not in lines:
                errors.append(f"{filename} 缺少必需段落：{section}")
        for section in forbidden_sections:
            if section in lines:
                errors.append(f"{filename} 重新展开了机器明细：{section}")
        if size_bytes > max_bytes:
            errors.append(f"{filename} 超过 {max_bytes} bytes：{size_bytes}")
        if line_count > max_lines:
            errors.append(f"{filename} 超过 {max_lines} 行：{line_count}")

        status_line = lines.index("## 当前状态") + 1 if "## 当前状态" in lines else 0
        next_line = lines.index("## 下一步") + 1 if "## 下一步" in lines else 0
        if status_line > status_max_line:
            errors.append(f"{filename} 当前状态出现过晚：第 {status_line} 行")
        if next_line > next_max_line:
            errors.append(f"{filename} 下一步出现过晚：第 {next_line} 行")

        status_text = section_body(lines, "## 当前状态")
        next_text = section_body(lines, "## 下一步")
        for token in required_status_tokens:
            if token not in status_text:
                errors.append(f"{filename} 当前状态缺少：{token}")
        for token in required_next_tokens:
            if token not in next_text:
                errors.append(f"{filename} 下一步缺少：{token}")
        if filename == "模型参数文件.md":
            for parameter_id in key_parameter_ids:
                if parameter_id not in text:
                    errors.append(f"{filename} 缺少合同关键参数：{parameter_id}")
        status_next_chars = len(re.sub(r"\s+", "", status_text + next_text))
        if status_next_chars > status_next_max_chars:
            errors.append(f"{filename} 状态与下一步超过两分钟摘要上限：{status_next_chars} 字符")
        if any(marker in text for marker in MOJIBAKE_MARKERS):
            errors.append(f"{filename} 命中乱码标记")

        reports.append(
            {
                "file": filename,
                "bytes": size_bytes,
                "lines": line_count,
                "status_heading_line": status_line,
                "next_heading_line": next_line,
                "status_and_next_chars": status_next_chars,
            }
        )
    return reports, errors


def audit_change_usage_map(database_dir: Path) -> tuple[dict[str, object], list[str]]:
    contract_path = database_dir / CHANGE_USAGE_MAP_CONTRACT
    if not contract_path.is_file():
        return {}, [f"缺少变化与使用地图合同：{CHANGE_USAGE_MAP_CONTRACT.as_posix()}"]
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {}, [f"变化与使用地图合同无法解析：{exc}"]

    errors: list[str] = []
    if contract.get("schema_version") != CHANGE_USAGE_MAP_SCHEMA:
        errors.append(f"变化与使用地图 schema 不匹配：{contract.get('schema_version')}")
    if contract.get("task_id") != "S05-P1-T3":
        errors.append("变化与使用地图必须绑定 S05-P1-T3")
    if contract.get("acceptance") != "用户能看到本次交付到底改变了什么。":
        errors.append("变化与使用地图 acceptance 不得弱化")
    for field, expected in CHANGE_USAGE_MAP_LIMITS.items():
        if contract.get(field) != expected:
            errors.append(f"变化与使用地图合同不得放宽 {field}：必须为 {expected}")

    categories = contract.get("change_categories")
    if not isinstance(categories, dict) or tuple(categories) != CHANGE_CATEGORY_NAMES:
        errors.append("变化与使用地图必须依次包含新增、修改、删除或隐藏")
        categories = {}
    category_counts: dict[str, int] = {}
    required_content: list[str] = []
    for category_name in CHANGE_CATEGORY_NAMES:
        items = categories.get(category_name)
        valid_items = [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []
        category_counts[category_name] = len(valid_items)
        if not valid_items or len(valid_items) != len(items or []):
            errors.append(f"变化类别缺少有效项目：{category_name}")
        for item in valid_items:
            name = str(item.get("name") or "").strip()
            description = str(item.get("description") or "").strip()
            task_refs = item.get("task_refs")
            if not name or not description or not isinstance(task_refs, list) or not task_refs:
                errors.append(f"变化项目缺少名称、说明或 Task 引用：{category_name}/{name or 'unnamed'}")
            required_content.extend([name, description])

    workflows = contract.get("workflows")
    valid_workflows = [item for item in workflows if isinstance(item, dict)] if isinstance(workflows, list) else []
    workflow_names = tuple(str(item.get("name") or "") for item in valid_workflows)
    if workflow_names != CORE_WORKFLOW_NAMES:
        errors.append("变化与使用地图必须精确定义五个核心用户流程")
    for index, workflow in enumerate(valid_workflows, start=1):
        if workflow.get("id") != f"FLOW-{index}":
            errors.append(f"核心流程 ID 顺序错误：FLOW-{index}")
        steps = workflow.get("steps")
        if not isinstance(steps, list) or len(steps) < 3 or not all(str(step).strip() for step in steps):
            errors.append(f"核心流程必须有至少三个步骤：{workflow.get('name')}")
        for field in ("name", "entry", "result", "current_state", "boundary"):
            value = str(workflow.get(field) or "").strip()
            if not value:
                errors.append(f"核心流程缺少 {field}：{workflow.get('name')}")
            else:
                required_content.append(value)

    path = database_dir / "人类可读" / CHANGE_USAGE_MAP_FILE
    text = ""
    if not path.is_file():
        errors.append(f"缺少变化与使用地图：{CHANGE_USAGE_MAP_FILE}")
    else:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{CHANGE_USAGE_MAP_FILE} 不是有效 UTF-8：{exc}")
    lines = text.splitlines()
    max_lines = int(contract.get("max_lines") or 0)
    max_bytes = int(contract.get("max_bytes") or 0)
    if len(lines) > max_lines:
        errors.append(f"变化与使用地图超过 {max_lines} 行：{len(lines)}")
    if len(text.encode("utf-8")) > max_bytes:
        errors.append(f"变化与使用地图超过 {max_bytes} bytes：{len(text.encode('utf-8'))}")
    if text and not text.startswith("# Memory Atlas v1.2.1 变化与使用地图\n"):
        errors.append("变化与使用地图缺少精确标题")
    for section in CHANGE_USAGE_MAP_REQUIRED_SECTIONS:
        if section not in lines:
            errors.append(f"变化与使用地图缺少段落：{section}")
    for category_name in CHANGE_CATEGORY_NAMES:
        if f"### {category_name}" not in lines:
            errors.append(f"变化与使用地图缺少变化类别：{category_name}")
    rendered_workflows = tuple(
        match.group(2)
        for line in lines
        if (match := re.fullmatch(r"### ([1-5])\. (.+)", line))
    )
    if rendered_workflows != CORE_WORKFLOW_NAMES:
        errors.append("变化与使用地图必须按固定顺序直接展示五个核心流程")
    for value in required_content:
        if value and value not in text:
            errors.append(f"变化与使用地图未呈现合同内容：{value[:60]}")
    for token in ("未推送 GitHub main", "未部署", "尚未完成"):
        if token not in text:
            errors.append(f"变化与使用地图缺少未交付边界：{token}")

    return {
        "file": CHANGE_USAGE_MAP_FILE,
        "bytes": len(text.encode("utf-8")),
        "lines": len(lines),
        "category_counts": category_counts,
        "workflow_count": len(valid_workflows),
        "workflow_names": list(workflow_names),
    }, errors


def normalize_reference_label(value: str) -> str:
    return " ".join(value.split()).casefold()


def markdown_link_targets(text: str) -> list[str]:
    """Return inline and reference-style Markdown targets, including images."""

    targets = [match.group(1) for match in INLINE_LINK_RE.finditer(text)]
    definitions = {
        normalize_reference_label(match.group(1)): match.group(2)
        for match in REFERENCE_DEFINITION_RE.finditer(text)
    }
    for match in REFERENCE_USE_RE.finditer(text):
        if match.end() < len(text) and text[match.end()] == "(":
            continue
        explicit_label = match.group(2)
        label = explicit_label if explicit_label else match.group(1)
        target = definitions.get(normalize_reference_label(label))
        if target is not None:
            targets.append(target)
    return targets


def classify_local_link(raw_target: str, *, source_path: Path, human_root: Path) -> tuple[str, str] | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    target = unquote(target)
    parsed = urlsplit(target)
    if parsed.scheme in {"http", "https", "mailto"}:
        return None
    if parsed.scheme or parsed.netloc:
        return ("unsupported", raw_target)
    if not parsed.path:
        return None

    candidate = Path(parsed.path)
    resolved = candidate.resolve() if candidate.is_absolute() else (source_path.parent / candidate).resolve()
    try:
        resolved.relative_to(human_root)
    except ValueError:
        return ("outside", raw_target)
    if not resolved.exists():
        return ("broken", raw_target)
    return None


def audit(database_dir: Path) -> dict[str, object]:
    human_dir = database_dir / "人类可读"
    errors: list[str] = []
    file_reports: list[dict[str, object]] = []

    if not human_dir.is_dir():
        return {"status": "FAIL", "human_dir": str(human_dir), "errors": ["人类可读目录不存在"]}

    human_root = human_dir.resolve()
    direct_files = sorted(path for path in human_dir.iterdir() if path.is_file())
    direct_names = {path.name for path in direct_files}
    nested_files = sorted(path for path in human_dir.rglob("*") if path.is_file() and path.parent != human_dir)
    nested_dirs = sorted(path for path in human_dir.rglob("*") if path.is_dir())

    if direct_names != EXPECTED_FILES:
        errors.append(
            "核心文件集合不一致："
            f"缺少={sorted(EXPECTED_FILES - direct_names)}，多出={sorted(direct_names - EXPECTED_FILES)}"
        )
    if len(direct_files) > 7:
        errors.append(f"核心文件超过 7 个：{len(direct_files)}")
    if nested_files or nested_dirs:
        errors.append(
            "人类目录必须保持浅层："
            f"nested_files={[str(path.relative_to(human_dir)) for path in nested_files]}，"
            f"nested_dirs={[str(path.relative_to(human_dir)) for path in nested_dirs]}"
        )

    for path in direct_files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{path.name} 不是有效 UTF-8：{exc}")
            continue

        chinese_chars = len(CHINESE_RE.findall(text))
        markdown_links = markdown_link_targets(text)
        local_link_errors: list[str] = []
        outside_link_errors: list[str] = []
        unsupported_link_errors: list[str] = []
        for raw_target in markdown_links:
            classification = classify_local_link(raw_target, source_path=path, human_root=human_root)
            if classification is None:
                continue
            kind, _ = classification
            if kind == "broken":
                local_link_errors.append(raw_target)
            elif kind == "outside":
                outside_link_errors.append(raw_target)
            else:
                unsupported_link_errors.append(raw_target)

        if not text.startswith("# "):
            errors.append(f"{path.name} 缺少一级中文标题")
        if "## 结论" not in text or "## 操作" not in text:
            errors.append(f"{path.name} 必须直接提供“结论”和“操作”")
        if chinese_chars < 250:
            errors.append(f"{path.name} 中文说明不足：{chinese_chars} 字")
        if any(marker in text for marker in MOJIBAKE_MARKERS):
            errors.append(f"{path.name} 命中乱码标记")
        if "Machine-readable boundary summary" in text:
            errors.append(f"{path.name} 包含旧机器边界摘要")
        if len(markdown_links) > 8:
            errors.append(f"{path.name} 链接过多，疑似链接索引：{len(markdown_links)}")
        if local_link_errors:
            errors.append(f"{path.name} 存在断链：{local_link_errors}")
        if outside_link_errors:
            errors.append(f"{path.name} 存在人类目录外链接：{outside_link_errors}")
        if unsupported_link_errors:
            errors.append(f"{path.name} 存在不支持的链接协议：{unsupported_link_errors}")

        file_reports.append(
            {
                "file": path.name,
                "lines": text.count("\n"),
                "chinese_chars": chinese_chars,
                "markdown_links": len(markdown_links),
                "broken_local_links": local_link_errors,
                "outside_human_dir_links": outside_link_errors,
                "unsupported_links": unsupported_link_errors,
            }
        )

    owner_entry_reports, owner_entry_errors = audit_owner_entries(database_dir)
    errors.extend(owner_entry_errors)
    change_usage_map_report, change_usage_map_errors = audit_change_usage_map(database_dir)
    errors.extend(change_usage_map_errors)

    return {
        "status": "PASS" if not errors else "FAIL",
        "human_dir": str(human_dir),
        "file_count": len(direct_files),
        "nested_file_count": len(nested_files),
        "files": file_reports,
        "owner_entries": owner_entry_reports,
        "change_usage_map": change_usage_map_report,
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="OpenAIDatabase directory; defaults to the script parent project.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = audit(args.database_dir.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
