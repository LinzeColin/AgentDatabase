#!/usr/bin/env python3
"""Audit the bounded Memory Atlas human plane and machine truth index."""

from __future__ import annotations

import argparse
import json
import re
from hashlib import sha256
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
MACHINE_TRUTH_INDEX_CONTRACT = Path("config/memory_atlas_machine_truth_index.json")
MACHINE_TRUTH_INDEX_SCHEMA = "memory_atlas.machine_truth_index.v1_2_1_s05_p2_t1"
MACHINE_TRUTH_INDEX_LIMITS = {"max_lines": 80, "max_bytes": 8500}
MACHINE_TRUTH_CONTRACT_KEYS = {
    "schema_version",
    "task_id",
    "acceptance",
    "max_lines",
    "max_bytes",
    "ownership_rules",
    "domains",
}
MACHINE_TRUTH_DOMAIN_KEYS = {"id", "label", "purpose", "entries"}
MACHINE_TRUTH_DOMAIN_TARGETS = {
    "requirements": (
        "docs/governance/roadmap.yaml",
        "config/memory_atlas_test_value_review.json",
    ),
    "source": ("config/data_sources/source_registry.json",),
    "model": (
        "docs/governance/model_registry.yaml",
        "docs/governance/formula_registry.yaml",
        "docs/governance/parameter_registry.csv",
        "docs/governance/project.yaml",
    ),
    "acceptance": (
        "config/memory_atlas_validator_profiles.json",
        "tests",
    ),
    "evidence": (
        "docs/governance/events.jsonl",
        "机器治理/证据与日志",
    ),
}
MACHINE_TRUTH_ENTRY_KEYS = {"path", "role", "owner", "mutability", "target_kind"}
MACHINE_TRUTH_MUTABILITY = {
    "canonical_editable",
    "generated_projection",
    "test_assertions",
    "append_only_evidence",
    "evidence_directory",
}
MACHINE_TRUTH_REQUIRED_SECTIONS = {
    "## 结论",
    "## 操作",
    "## 五域索引",
    "## 变更规则",
    "## 边界",
}
MACHINE_PLANE_CLEANUP_CONTRACT = Path("config/memory_atlas_machine_plane_cleanup.json")
MACHINE_PLANE_CLEANUP_SCHEMA = "memory_atlas.machine_plane_cleanup.v1_2_1_s05_p2_t2"
MACHINE_PLANE_CLEANUP_SOURCE_COMMIT = "187577cc93f2c163ef120f2d7c3e0cbc3d71b6ad"
MACHINE_PLANE_CLEANUP_BATCH = "S05-P2-T2-machine-humanized-records"
MACHINE_PLANE_CLEANUP_TOP_KEYS = {
    "schema_version",
    "task_id",
    "acceptance",
    "taskpack",
    "source_commit",
    "batch",
    "inventory_before",
    "inventory_after",
    "protected_sets",
    "candidates",
}
MACHINE_PLANE_CLEANUP_CANDIDATE_KEYS = {
    "path",
    "category",
    "references",
    "runtime_dependency",
    "replacement_source",
    "reason",
    "restore_method",
    "batch",
    "validation",
    "approval",
}
MACHINE_PLANE_CLEANUP_CANDIDATES = (
    "机器治理/参数与公式/README.md",
    "机器治理/可视化配置/README.md",
    "机器治理/同步与备份/README.md",
    "机器治理/数据契约/README.md",
    "机器治理/测试与验收/README.md",
    "机器治理/行为智能模型/README.md",
    "机器治理/证据与日志/README.md",
    "机器治理/运行门禁/README.md",
)
MACHINE_PLANE_CLEANUP_INVENTORY_BEFORE = {
    "machine_file_count": 161,
    "stage_humanized_readme_count": 8,
    "stage_humanized_readme_lines": 1948,
    "stage_humanized_readme_bytes": 90721,
}
MACHINE_PLANE_CLEANUP_INVENTORY_AFTER = {
    "machine_file_count": 182,
    "nested_readme_count": 0,
    "root_index_count": 1,
    "current_release_count": 1,
    "active_config_count": 45,
    "evidence_payload_count": 135,
}
MACHINE_PLANE_PROTECTED_SCOPES = {
    "root_index": "机器治理/README.md",
    "current_release": "机器治理/发布快照/**",
    "active_configs": "机器治理/** excluding README.md, 发布快照/** and 证据与日志/**",
    "evidence_payload": "机器治理/证据与日志/** excluding README.md",
}
MACHINE_PLANE_PROTECTED_EXPECTED = {
    "root_index": {
        "file_count": 1,
        "bytes": 4702,
        "manifest_sha256": "01aa229b2ba99e241ae57a8d573681a36473159869660201bcf3dc8a0232eece",
    },
    "current_release": {
        "file_count": 1,
        "bytes": 549,
        "manifest_sha256": "a8293b7357085faae11f32beb2403b1bc960bff29bec70b135aed87f4965c8a0",
    },
    "active_configs": {
        "file_count": 45,
        "bytes": 129445,
        "manifest_sha256": "ccd09afc34cceac2abc4522868c7a0a1dd143f7eba0d6554ea85944331568847",
    },
    "evidence_payload": {
        "file_count": 135,
        "bytes": 25652772,
        "manifest_sha256": "603d29786d4cd64dc8858702f6e21c32cebc80ca994ddcadae8c902a0930dc8c",
    },
}
MACHINE_PLANE_PROTECTED_KEYS = {"id", "path_scope", "file_count", "bytes", "manifest_sha256"}
HUMAN_MACHINE_GATE_MARKERS = (
    "validate:" + "v1.2-",
    "phase_" + "s",
    "stage_" + "s",
    "ACC-" + "MA-V12",
    "MA-" + "V12-",
)
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
        matched_machine_markers = [marker for marker in HUMAN_MACHINE_GATE_MARKERS if marker in text]
        if matched_machine_markers or re.search(r"\b[a-f0-9]{40}(?:[a-f0-9]{24})?\b", text):
            errors.append(f"{filename} 被机器门禁、状态或 hash 污染：{matched_machine_markers}")

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


def audit_machine_truth_index(database_dir: Path) -> tuple[dict[str, object], list[str]]:
    contract_path = database_dir / MACHINE_TRUTH_INDEX_CONTRACT
    if not contract_path.is_file():
        return {}, [f"缺少机器真相索引合同：{MACHINE_TRUTH_INDEX_CONTRACT.as_posix()}"]
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {}, [f"机器真相索引合同无法解析：{exc}"]

    errors: list[str] = []
    if set(contract) != MACHINE_TRUTH_CONTRACT_KEYS:
        errors.append("机器真相索引合同只能保存 schema、边界、所有权规则与五域")
    if contract.get("schema_version") != MACHINE_TRUTH_INDEX_SCHEMA:
        errors.append(f"机器真相索引 schema 不匹配：{contract.get('schema_version')}")
    if contract.get("task_id") != "S05-P2-T1":
        errors.append("机器真相索引必须绑定 S05-P2-T1")
    if contract.get("acceptance") != "同一参数、公式、状态只能有一个可执行源。":
        errors.append("机器真相索引 acceptance 不得弱化")
    for field, expected in MACHINE_TRUTH_INDEX_LIMITS.items():
        if contract.get(field) != expected:
            errors.append(f"机器真相索引合同不得放宽 {field}：必须为 {expected}")

    domains = contract.get("domains")
    valid_domains = [item for item in domains if isinstance(item, dict)] if isinstance(domains, list) else []
    if not isinstance(domains, list) or len(valid_domains) != len(domains):
        errors.append("机器真相索引 domains 必须全部为对象")
    domain_ids = tuple(str(item.get("id") or "") for item in valid_domains)
    expected_domain_ids = tuple(MACHINE_TRUTH_DOMAIN_TARGETS)
    if domain_ids != expected_domain_ids:
        errors.append("机器真相索引必须精确定义 requirements/source/model/acceptance/evidence 五域")

    seen_paths: set[str] = set()
    domain_counts: dict[str, int] = {}
    for domain in valid_domains:
        domain_id = str(domain.get("id") or "")
        if set(domain) != MACHINE_TRUTH_DOMAIN_KEYS:
            errors.append(f"机器真相域只能保存 id、label、purpose 与 entries：{domain_id}")
        entries = domain.get("entries")
        valid_entries = [item for item in entries if isinstance(item, dict)] if isinstance(entries, list) else []
        if not isinstance(entries, list) or len(valid_entries) != len(entries):
            errors.append(f"机器真相域 entries 必须全部为对象：{domain_id}")
        domain_counts[domain_id] = len(valid_entries)
        expected_paths = MACHINE_TRUTH_DOMAIN_TARGETS.get(domain_id, ())
        actual_paths = tuple(str(item.get("path") or "") for item in valid_entries)
        if actual_paths != expected_paths:
            errors.append(f"机器真相索引 {domain_id} canonical targets 不得变更：{actual_paths}")
        if not str(domain.get("label") or "").strip() or not str(domain.get("purpose") or "").strip():
            errors.append(f"机器真相域缺少 label 或 purpose：{domain_id}")
        for entry in valid_entries:
            if set(entry) != MACHINE_TRUTH_ENTRY_KEYS:
                errors.append(f"机器真相索引条目只能保存路径与所有权字段：{domain_id}/{entry.get('path')}")
            raw_path = str(entry.get("path") or "")
            candidate = Path(raw_path)
            if not raw_path or candidate.is_absolute() or ".." in candidate.parts:
                errors.append(f"机器真相索引路径必须为项目内相对路径：{raw_path}")
                continue
            if raw_path in seen_paths:
                errors.append(f"机器真相索引目标重复：{raw_path}")
            seen_paths.add(raw_path)
            target = database_dir / candidate
            target_kind = str(entry.get("target_kind") or "")
            if target_kind == "file" and not target.is_file():
                errors.append(f"机器真相索引文件目标不存在：{raw_path}")
            elif target_kind == "directory" and not target.is_dir():
                errors.append(f"机器真相索引目录目标不存在：{raw_path}")
            elif target_kind not in {"file", "directory"}:
                errors.append(f"机器真相索引 target_kind 无效：{raw_path}/{target_kind}")
            if not str(entry.get("role") or "").strip() or not str(entry.get("owner") or "").strip():
                errors.append(f"机器真相索引条目缺少 role 或 owner：{raw_path}")
            if entry.get("mutability") not in MACHINE_TRUTH_MUTABILITY:
                errors.append(f"机器真相索引 mutability 无效：{raw_path}/{entry.get('mutability')}")

    path = database_dir / "机器治理" / "README.md"
    text = ""
    if not path.is_file():
        errors.append("缺少机器真相索引：机器治理/README.md")
    else:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"机器治理/README.md 不是有效 UTF-8：{exc}")
    lines = text.splitlines()
    if text and not text.startswith("# Memory Atlas 机器真相索引\n"):
        errors.append("机器真相索引缺少精确标题")
    for section in MACHINE_TRUTH_REQUIRED_SECTIONS:
        if section not in lines:
            errors.append(f"机器真相索引缺少段落：{section}")
    rendered_domains = tuple(
        match.group(1)
        for line in lines
        if (match := re.fullmatch(r"### (requirements|source|model|acceptance|evidence)｜.+", line))
    )
    if rendered_domains != expected_domain_ids:
        errors.append("机器真相索引必须按固定顺序直接展示五个真相域")
    for raw_path in seen_paths:
        if f"[{raw_path}]" not in text:
            errors.append(f"机器真相索引未呈现 canonical target：{raw_path}")
    max_lines = int(contract.get("max_lines") or 0)
    max_bytes = int(contract.get("max_bytes") or 0)
    if len(lines) > max_lines:
        errors.append(f"机器真相索引超过 {max_lines} 行：{len(lines)}")
    if len(text.encode("utf-8")) > max_bytes:
        errors.append(f"机器真相索引超过 {max_bytes} bytes：{len(text.encode('utf-8'))}")
    legacy_validator_prefix = "validate:" + "v1.2-"
    for marker in ("历史复验兼容记录", legacy_validator_prefix, "No GitHub main upload", "phase_", "stage_s"):
        if marker in text:
            errors.append(f"机器真相索引复制了旧状态或命令：{marker}")
    if re.search(r"\b(?:PARAM|FORM)-[A-Z0-9-]+\b", text):
        errors.append("机器真相索引复制了参数或公式 ID")

    return {
        "file": "机器治理/README.md",
        "bytes": len(text.encode("utf-8")),
        "lines": len(lines),
        "domain_count": len(valid_domains),
        "domain_counts": domain_counts,
        "target_count": len(seen_paths),
    }, errors


def validate_machine_plane_cleanup_contract(contract: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if set(contract) != MACHINE_PLANE_CLEANUP_TOP_KEYS:
        errors.append("机器平面清理合同字段集合不匹配")
    if contract.get("schema_version") != MACHINE_PLANE_CLEANUP_SCHEMA:
        errors.append("机器平面清理合同 schema 不匹配")
    if contract.get("task_id") != "S05-P2-T2":
        errors.append("机器平面清理合同必须绑定 S05-P2-T2")
    if contract.get("acceptance") != "机器门禁不得污染人类文件。":
        errors.append("机器平面清理 acceptance 不得弱化")
    if contract.get("source_commit") != MACHINE_PLANE_CLEANUP_SOURCE_COMMIT:
        errors.append("机器平面清理恢复基线不得变更")
    if contract.get("batch") != MACHINE_PLANE_CLEANUP_BATCH:
        errors.append("机器平面清理 batch 不得变更")
    if contract.get("taskpack") != {
        "filename": "v1.2.1_四线16Stage质量收敛升级_TaskPack.zip",
        "sha256": "db59f4db3ac02845fb3cde346a301cba64146c81c7ba19168f52c27e82ddd0f1",
    }:
        errors.append("机器平面清理必须绑定权威 TaskPack 文件名与 SHA-256")
    if contract.get("inventory_before") != MACHINE_PLANE_CLEANUP_INVENTORY_BEFORE:
        errors.append("机器平面清理 before inventory 不得变更")
    if contract.get("inventory_after") != MACHINE_PLANE_CLEANUP_INVENTORY_AFTER:
        errors.append("机器平面清理 after inventory 不得变更")

    protected_sets = contract.get("protected_sets")
    valid_protected = [item for item in protected_sets if isinstance(item, dict)] if isinstance(protected_sets, list) else []
    protected_ids = tuple(str(item.get("id") or "") for item in valid_protected)
    if protected_ids != tuple(MACHINE_PLANE_PROTECTED_SCOPES):
        errors.append("机器平面清理必须精确定义四个受保护集合")
    if not isinstance(protected_sets, list) or len(valid_protected) != len(protected_sets):
        errors.append("机器平面 protected_sets 必须全部为对象")
    for item in valid_protected:
        set_id = str(item.get("id") or "")
        if set(item) != MACHINE_PLANE_PROTECTED_KEYS:
            errors.append(f"机器平面受保护集合字段不匹配：{set_id}")
        if item.get("path_scope") != MACHINE_PLANE_PROTECTED_SCOPES.get(set_id):
            errors.append(f"机器平面受保护 scope 不得变更：{set_id}")
        expected_item = {
            "id": set_id,
            "path_scope": MACHINE_PLANE_PROTECTED_SCOPES.get(set_id),
            **MACHINE_PLANE_PROTECTED_EXPECTED.get(set_id, {}),
        }
        if item != expected_item:
            errors.append(f"机器平面受保护基线不得变更：{set_id}")
        if not isinstance(item.get("file_count"), int) or int(item.get("file_count") or 0) <= 0:
            errors.append(f"机器平面受保护 file_count 无效：{set_id}")
        if not isinstance(item.get("bytes"), int) or int(item.get("bytes") or 0) <= 0:
            errors.append(f"机器平面受保护 bytes 无效：{set_id}")
        if not re.fullmatch(r"[a-f0-9]{64}", str(item.get("manifest_sha256") or "")):
            errors.append(f"机器平面受保护 manifest SHA-256 无效：{set_id}")

    candidates = contract.get("candidates")
    valid_candidates = [item for item in candidates if isinstance(item, dict)] if isinstance(candidates, list) else []
    candidate_paths = tuple(str(item.get("path") or "") for item in valid_candidates)
    if candidate_paths != MACHINE_PLANE_CLEANUP_CANDIDATES:
        errors.append("机器平面清理候选必须精确为八个逐 Stage README")
    if not isinstance(candidates, list) or len(valid_candidates) != len(candidates):
        errors.append("机器平面清理 candidates 必须全部为对象")
    for item in valid_candidates:
        path = str(item.get("path") or "")
        if set(item) != MACHINE_PLANE_CLEANUP_CANDIDATE_KEYS:
            errors.append(f"机器平面清理候选字段不匹配：{path}")
        if item.get("category") != "delete" or item.get("approval") != "approved":
            errors.append(f"机器平面只允许删除已批准候选：{path}")
        if item.get("batch") != MACHINE_PLANE_CLEANUP_BATCH:
            errors.append(f"机器平面候选 batch 不匹配：{path}")
        expected_restore = (
            f"git restore --source={MACHINE_PLANE_CLEANUP_SOURCE_COMMIT} -- OpenAIDatabase/{path}"
        )
        if item.get("restore_method") != expected_restore:
            errors.append(f"机器平面候选缺少精确 Git 恢复命令：{path}")
        for field in ("runtime_dependency", "replacement_source", "reason"):
            if not str(item.get(field) or "").strip():
                errors.append(f"机器平面候选缺少 {field}：{path}")
        for field in ("references", "validation"):
            values = item.get(field)
            if not isinstance(values, list) or not values or not all(isinstance(value, str) and value for value in values):
                errors.append(f"机器平面候选 {field} 必须为非空字符串列表：{path}")
    return errors


def machine_plane_manifest(paths: list[Path], database_dir: Path) -> dict[str, object]:
    files = sorted(path for path in paths if path.is_file())
    rows = "".join(
        f"{path.relative_to(database_dir).as_posix()}\t{sha256(path.read_bytes()).hexdigest()}\n"
        for path in files
    )
    return {
        "file_count": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "manifest_sha256": sha256(rows.encode("utf-8")).hexdigest(),
    }


def current_machine_plane_protected_sets(database_dir: Path) -> dict[str, dict[str, object]]:
    machine_dir = database_dir / "机器治理"
    return {
        "root_index": machine_plane_manifest([machine_dir / "README.md"], database_dir),
        "current_release": machine_plane_manifest(list((machine_dir / "发布快照").rglob("*")), database_dir),
        "active_configs": machine_plane_manifest(
            [
                path
                for path in machine_dir.rglob("*")
                if path.is_file()
                and path.name != "README.md"
                and "发布快照" not in path.parts
                and "证据与日志" not in path.parts
            ],
            database_dir,
        ),
        "evidence_payload": machine_plane_manifest(
            [
                path
                for path in (machine_dir / "证据与日志").rglob("*")
                if path.is_file() and path.name != "README.md"
            ],
            database_dir,
        ),
    }


def audit_machine_plane_cleanup(
    database_dir: Path,
    *,
    required: bool,
) -> tuple[dict[str, object], list[str]]:
    contract_path = database_dir / MACHINE_PLANE_CLEANUP_CONTRACT
    if not contract_path.is_file():
        if required:
            return {}, [f"缺少机器平面清理合同：{MACHINE_PLANE_CLEANUP_CONTRACT.as_posix()}"]
        return {}, []
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {}, [f"机器平面清理合同无法解析：{exc}"]
    if not isinstance(contract, dict):
        return {}, ["机器平面清理合同必须为对象"]

    errors = validate_machine_plane_cleanup_contract(contract)
    for path in MACHINE_PLANE_CLEANUP_CANDIDATES:
        if (database_dir / path).exists():
            errors.append(f"已批准的逐 Stage 机器 README 仍存在：{path}")

    machine_dir = database_dir / "机器治理"
    machine_files = sorted(path for path in machine_dir.rglob("*") if path.is_file())
    nested_readmes = sorted(
        path.relative_to(database_dir).as_posix()
        for path in machine_dir.rglob("README.md")
        if path != machine_dir / "README.md"
    )
    if len(machine_files) != MACHINE_PLANE_CLEANUP_INVENTORY_AFTER["machine_file_count"]:
        errors.append(f"精简后机器文件数不匹配：{len(machine_files)}")
    if nested_readmes:
        errors.append(f"机器平面仍有嵌套人类化 README：{nested_readmes}")

    actual_sets = current_machine_plane_protected_sets(database_dir)
    for set_id in MACHINE_PLANE_PROTECTED_SCOPES:
        if actual_sets.get(set_id) != MACHINE_PLANE_PROTECTED_EXPECTED.get(set_id):
            errors.append(f"机器平面受保护集合发生漂移：{set_id}")

    builder_path = database_dir / "scripts" / "build_memory_atlas_agent_collaboration.py"
    builder_text = builder_path.read_text(encoding="utf-8") if builder_path.is_file() else ""
    deleted_runtime_ref = "机器治理/运行门禁/README.md"
    if deleted_runtime_ref in builder_text:
        errors.append("agent collaboration builder 仍引用已删除运行门禁 README")
    if "docs/governance/roadmap.yaml" not in builder_text:
        errors.append("agent collaboration builder 未迁移到 current governance roadmap")

    derived_report_path = (
        database_dir / "data" / "derived" / "agent_collaboration" / "agent_collaboration_quality_report.json"
    )
    try:
        derived_report = json.loads(derived_report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"agent collaboration derived report 无法解析：{exc}")
        derived_report = {}
    evidence_items: list[dict[str, object]] = []
    pending: list[object] = [derived_report]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            if "ref_id" in item and "path" in item:
                evidence_items.append(item)
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    stale_evidence = [
        item
        for item in evidence_items
        if item.get("path") == deleted_runtime_ref or item.get("ref_id") == "s08p1_run_gate"
    ]
    migrated_evidence = [
        item
        for item in evidence_items
        if item.get("path") == "docs/governance/roadmap.yaml"
        and item.get("ref_id") == "s08p1_governance_roadmap"
    ]
    if stale_evidence:
        errors.append("agent collaboration derived report 仍引用已删除运行门禁 README")
    if not migrated_evidence:
        errors.append("agent collaboration derived report 未迁移到 current governance roadmap")

    return {
        "contract": MACHINE_PLANE_CLEANUP_CONTRACT.as_posix(),
        "candidate_count": len(MACHINE_PLANE_CLEANUP_CANDIDATES),
        "deleted_count": sum(not (database_dir / path).exists() for path in MACHINE_PLANE_CLEANUP_CANDIDATES),
        "machine_file_count": len(machine_files),
        "nested_readmes": nested_readmes,
        "protected_sets": actual_sets,
        "migrated_derived_evidence_refs": len(migrated_evidence),
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


def audit(database_dir: Path, *, require_machine_cleanup: bool | None = None) -> dict[str, object]:
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
        matched_machine_markers = [marker for marker in HUMAN_MACHINE_GATE_MARKERS if marker in text]
        if matched_machine_markers or re.search(r"\b[a-f0-9]{40}(?:[a-f0-9]{24})?\b", text):
            errors.append(f"{path.name} 被机器门禁、状态或 hash 污染：{matched_machine_markers}")
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
    machine_truth_index_report, machine_truth_index_errors = audit_machine_truth_index(database_dir)
    errors.extend(machine_truth_index_errors)
    cleanup_required = (
        (database_dir / MACHINE_PLANE_CLEANUP_CONTRACT).is_file()
        if require_machine_cleanup is None
        else require_machine_cleanup
    )
    machine_plane_cleanup_report, machine_plane_cleanup_errors = audit_machine_plane_cleanup(
        database_dir,
        required=cleanup_required,
    )
    errors.extend(machine_plane_cleanup_errors)

    return {
        "status": "PASS" if not errors else "FAIL",
        "human_dir": str(human_dir),
        "file_count": len(direct_files),
        "nested_file_count": len(nested_files),
        "files": file_reports,
        "owner_entries": owner_entry_reports,
        "change_usage_map": change_usage_map_report,
        "machine_truth_index": machine_truth_index_report,
        "machine_plane_cleanup": machine_plane_cleanup_report,
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
    report = audit(args.database_dir.resolve(), require_machine_cleanup=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
