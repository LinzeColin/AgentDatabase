from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set

from .common import TeleiosisError, atomic_write_json, canonical_json_hash, read_json, safe_relative_path

PROJECT_INPUT_FIELDS = [
    "project_name", "target_repository", "target_area", "target_domain", "runtime_node",
    "current_phase", "product_version", "taskpack_version", "owner_approved_scope",
    "resource_ceiling", "cost_ceiling", "required_integrations", "forbidden_dependencies",
    "production_side_effect_authorization",
]
TASK_FIELDS = {
    "id", "category", "input", "output", "dependencies", "implementation_steps", "acceptance",
    "oracle", "test", "threshold", "evidence", "risk", "rollback", "stop_condition",
}
TASK_CATEGORIES = {"implementation", "testing", "remediation", "review", "research", "release"}
ALLOWED_PHASES = {
    "CONTEXT_CAPTURE", "RESEARCH_AND_REUSE", "PREBUILD", "TEN_LENS_REVIEW", "REMEDIATION",
    "BUILDER_READINESS", "OWNER_GATE", "SEALED_TASKPACK", "BUILD_LAST_MILE", "FROZEN_CANDIDATE",
    "VERIFY_AND_RELEASE", "POST_DEPLOY_OBSERVATION",
}


def validate_project_input(value: Mapping[str, Any]) -> Dict[str, Any]:
    missing = [field for field in PROJECT_INPUT_FIELDS if field not in value]
    if missing:
        raise TeleiosisError("PROJECT_INPUT_MISSING", "Project Input 缺少冻结字段。", {"missing": missing})
    for field in PROJECT_INPUT_FIELDS:
        item = value[field]
        if item is None or item == "" or item == []:
            raise TeleiosisError("PROJECT_INPUT_EMPTY", "Project Input 字段为空。", {"field": field})
    if value["current_phase"] not in ALLOWED_PHASES:
        raise TeleiosisError("PROJECT_PHASE_INVALID", "current_phase 不在唯一状态机内。", {"phase": value["current_phase"]})
    if not isinstance(value["required_integrations"], list) or not isinstance(value["forbidden_dependencies"], list):
        raise TeleiosisError("PROJECT_INPUT_LIST", "required_integrations 与 forbidden_dependencies 必须是列表。")
    result = dict(value)
    result["schema_version"] = "teleiosis.project_input.v5"
    result["frozen_hash"] = canonical_json_hash(result)
    return result


def _validate_dag(tasks: List[Mapping[str, Any]]) -> Dict[str, Any]:
    if not tasks:
        raise TeleiosisError("DAG_EMPTY", "任务 DAG 为空。")
    by_id: Dict[str, Mapping[str, Any]] = {}
    categories: Set[str] = set()
    for task in tasks:
        missing = sorted(TASK_FIELDS - set(task))
        if missing:
            raise TeleiosisError("DAG_TASK_INCOMPLETE", "任务缺少完整执行合同字段。", {"task": task.get("id"), "missing": missing})
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id or task_id in by_id:
            raise TeleiosisError("DAG_TASK_ID", "任务 ID 缺失或重复。", {"task": task_id})
        by_id[task_id] = task
        category = task.get("category")
        if category not in TASK_CATEGORIES:
            raise TeleiosisError("DAG_CATEGORY", "任务类别不在冻结六类中。", {"task": task_id, "category": category})
        categories.add(str(category))
        if not isinstance(task.get("dependencies"), list):
            raise TeleiosisError("DAG_DEPENDENCIES", "dependencies 必须为列表。", {"task": task_id})
        if not isinstance(task.get("implementation_steps"), list) or not task["implementation_steps"]:
            raise TeleiosisError("DAG_STEPS", "implementation_steps 不能为空。", {"task": task_id})
        for field in TASK_FIELDS - {"dependencies", "implementation_steps", "category", "id"}:
            if not isinstance(task.get(field), str) or not task[field].strip():
                raise TeleiosisError("DAG_FIELD_EMPTY", "任务执行字段为空。", {"task": task_id, "field": field})
        for marker in ("real-time soak", "wait 24h", "等待观察期", "再次审批"):
            if marker.lower() in " ".join(str(task.get(f, "")) for f in TASK_FIELDS).lower():
                raise TeleiosisError("DAG_WAIT_NODE", "任务 DAG 包含真实等待或重复审批。", {"task": task_id, "marker": marker})
    if categories != TASK_CATEGORIES:
        raise TeleiosisError("DAG_CATEGORY_COVERAGE", "任务 DAG 未覆盖六类工作。", {"missing": sorted(TASK_CATEGORIES - categories)})
    for task_id, task in by_id.items():
        for dep in task["dependencies"]:
            if dep not in by_id:
                raise TeleiosisError("DAG_MISSING_DEP", "任务依赖不存在。", {"task": task_id, "dependency": dep})
    visiting: Set[str] = set()
    visited: Set[str] = set()
    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise TeleiosisError("DAG_CYCLE", "任务 DAG 存在循环。", {"task": task_id})
        if task_id in visited:
            return
        visiting.add(task_id)
        for dep in by_id[task_id]["dependencies"]:
            visit(dep)
        visiting.remove(task_id)
        visited.add(task_id)
    for task_id in by_id:
        visit(task_id)
    return {"tasks": len(tasks), "categories": sorted(categories), "acyclic": True}


def validate_traceability(acceptance: Mapping[str, Any], dag: Mapping[str, Any], trace: Mapping[str, Any], root: Optional[Path] = None) -> Dict[str, Any]:
    criteria = acceptance.get("criteria")
    tasks = dag.get("tasks")
    entries = trace.get("entries")
    if not isinstance(criteria, list) or not isinstance(tasks, list) or not isinstance(entries, list):
        raise TeleiosisError("TRACE_INPUT", "Acceptance、DAG 或 Traceability 格式不正确。")
    _validate_dag(tasks)
    criterion_ids = {item.get("id") for item in criteria if isinstance(item, dict)}
    task_ids = {item.get("id") for item in tasks if isinstance(item, dict)}
    mapped = {item.get("requirement_id") for item in entries if isinstance(item, dict)}
    if criterion_ids != mapped:
        raise TeleiosisError("TRACE_COVERAGE", "Acceptance 与 Traceability 未一一对应。", {"missing": sorted(criterion_ids - mapped), "extra": sorted(mapped - criterion_ids)})
    for entry in entries:
        if not entry.get("task_ids") or any(task_id not in task_ids for task_id in entry["task_ids"]):
            raise TeleiosisError("TRACE_TASK", "Traceability 引用了不存在的任务。", {"requirement": entry.get("requirement_id")})
        for field in ("test", "oracle", "evidence", "artifacts"):
            if not entry.get(field):
                raise TeleiosisError("TRACE_FIELD", "Traceability 条目不完整。", {"requirement": entry.get("requirement_id"), "field": field})
        if root is not None:
            paths = [entry["evidence"], *entry.get("artifacts", [])]
            for rel_text in paths:
                rel_text = rel_text[:-1] if isinstance(rel_text, str) and rel_text.endswith("/") else rel_text
                path = root / safe_relative_path(rel_text)
                if not path.exists() or path.is_symlink():
                    raise TeleiosisError("TRACE_ARTIFACT", "Traceability 制品不存在或不安全。", {"path": rel_text})
    return {"criteria": len(criterion_ids), "mapped": len(mapped), "tasks": len(task_ids)}


def validate_taskpack(root: Path) -> Dict[str, Any]:
    project_input = validate_project_input(read_json(root / "metadata/project-input.json"))
    acceptance = read_json(root / "ACCEPTANCE_CONTRACT.json")
    dag = read_json(root / "TASK_DAG.json")
    trace = read_json(root / "TRACEABILITY_MATRIX.json")
    trace_result = validate_traceability(acceptance, dag, trace, root=root)
    result = {
        "schema_version": "teleiosis.taskpack_validation.v5",
        "status": "PASS",
        "project_input_hash": project_input["frozen_hash"],
        "traceability": trace_result,
        "constraints": {
            "real_time_wait_nodes": 0,
            "duplicate_approval_nodes": 0,
            "canonical_source": "CANONICAL_STATE.json",
        },
    }
    result["validation_hash"] = canonical_json_hash(result)
    return result


def fresh_builder_simulation(root: Path) -> Dict[str, Any]:
    taskpack = validate_taskpack(root)
    data = read_json(root / "metadata/last-mile-tasks.json")
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        raise TeleiosisError("LAST_MILE_TASKS", "last-mile-tasks.json 缺少 tasks。")
    required = {"id", "environment_bound_reason", "goal", "command", "input", "expected", "failure_branch", "stop_condition", "rollback", "evidence"}
    for task in tasks:
        missing = sorted(required - set(task))
        if missing:
            raise TeleiosisError("LAST_MILE_TASK_INCOMPLETE", "最后一公里任务不完整。", {"task": task.get("id"), "missing": missing})
        if not task.get("environment_bound_reason"):
            raise TeleiosisError("LAST_MILE_NOT_ENVIRONMENT_BOUND", "最后一公里任务缺少环境绑定理由。", {"task": task.get("id")})
    result = {
        "schema_version": "teleiosis.fresh_builder_simulation.v5",
        "status": "ACCEPTANCE_PASS",
        "taskpack_validation_hash": taskpack["validation_hash"],
        "research_reopened": False,
        "only_environment_bound_unknowns_remain": True,
        "environment_bound_tasks": len(tasks),
    }
    result["simulation_hash"] = canonical_json_hash(result)
    return result
