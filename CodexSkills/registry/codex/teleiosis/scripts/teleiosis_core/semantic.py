from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set

from .common import (
    TeleiosisError,
    atomic_write_json,
    canonical_json_hash,
    ensure_plain_directory,
    read_json,
    safe_relative_path,
    sha256_file,
)

ALLOWED_CLASSIFICATIONS = {
    "satisfied", "apply", "adapt", "equivalent", "conflict", "blocked", "obsolete"
}
REQUIRED_TASK_FIELDS = {"id", "semantic_goal", "impact_boundary", "paths"}


def _ensure_string_list(value: Any, field: str, task_id: str) -> List[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise TeleiosisError("SEMANTIC_SPEC_FIELD", "Stage 0 任务字段必须是非空字符串列表。", {"task": task_id, "field": field})
    return list(value)


def validate_semantic_spec(spec: Mapping[str, Any]) -> Dict[str, Any]:
    if spec.get("schema_version") != "teleiosis.semantic_reconcile_spec.v5":
        raise TeleiosisError("SEMANTIC_SPEC_SCHEMA", "Semantic Reconcile spec schema 不正确。")
    tasks = spec.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise TeleiosisError("SEMANTIC_SPEC_EMPTY", "Semantic Reconcile 任务为空。")
    ids: Set[str] = set()
    normalized: List[Dict[str, Any]] = []
    for raw in tasks:
        if not isinstance(raw, dict):
            raise TeleiosisError("SEMANTIC_TASK_TYPE", "Semantic Reconcile 任务必须是对象。")
        missing = sorted(REQUIRED_TASK_FIELDS - set(raw))
        if missing:
            raise TeleiosisError("SEMANTIC_TASK_INCOMPLETE", "Semantic Reconcile 任务字段不完整。", {"missing": missing})
        task_id = raw.get("id")
        if not isinstance(task_id, str) or not task_id.strip() or task_id in ids:
            raise TeleiosisError("SEMANTIC_TASK_ID", "Semantic Reconcile 任务 ID 缺失或重复。", {"id": task_id})
        ids.add(task_id)
        paths = _ensure_string_list(raw.get("paths"), "paths", task_id)
        for value in paths:
            safe_relative_path(value)
        required_paths = raw.get("required_paths", [])
        if required_paths:
            _ensure_string_list(required_paths, "required_paths", task_id)
            for value in required_paths:
                safe_relative_path(value)
        expected_hashes = raw.get("expected_hashes", {})
        if not isinstance(expected_hashes, dict):
            raise TeleiosisError("SEMANTIC_HASH_MAP", "expected_hashes 必须是对象。", {"task": task_id})
        for rel, digest in expected_hashes.items():
            safe_relative_path(str(rel))
            if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise TeleiosisError("SEMANTIC_HASH", "expected_hashes 包含非法 SHA-256。", {"task": task_id, "path": rel})
        markers = raw.get("equivalence_markers", {})
        if not isinstance(markers, dict) or any(not isinstance(v, list) for v in markers.values()):
            raise TeleiosisError("SEMANTIC_MARKERS", "equivalence_markers 必须是路径到字符串列表的映射。", {"task": task_id})
        for rel, values in markers.items():
            safe_relative_path(str(rel))
            _ensure_string_list(values, "equivalence_markers", task_id)
        blockers = raw.get("blockers", [])
        if blockers:
            _ensure_string_list(blockers, "blockers", task_id)
            for value in blockers:
                safe_relative_path(value)
        conflict_markers = raw.get("conflict_markers", [])
        if conflict_markers:
            _ensure_string_list(conflict_markers, "conflict_markers", task_id)
        normalized.append(dict(raw))
    return {"schema_version": spec["schema_version"], "tasks": normalized, "spec_hash": canonical_json_hash(spec)}


def _read_text_if_small(path: Path, limit: int = 2 * 1024 * 1024) -> str:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > limit:
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


def classify_task(repository: Path, task: Mapping[str, Any]) -> Dict[str, Any]:
    task_id = str(task["id"])
    if task.get("obsolete") is True:
        return {"task_id": task_id, "classification": "obsolete", "reason": "任务已被当前权威明确废止。", "evidence": []}

    missing_blockers = []
    for rel_text in task.get("blockers", []):
        path = repository / safe_relative_path(rel_text)
        if not path.exists():
            missing_blockers.append(rel_text)
    if missing_blockers:
        return {"task_id": task_id, "classification": "blocked", "reason": "缺少执行前置文件。", "evidence": missing_blockers}

    texts: List[str] = []
    present: List[str] = []
    missing: List[str] = []
    for rel_text in task["paths"]:
        path = repository / safe_relative_path(rel_text)
        if path.exists() and not path.is_symlink():
            present.append(rel_text)
            text = _read_text_if_small(path)
            if text:
                texts.append(text)
        else:
            missing.append(rel_text)

    combined = "\n".join(texts)
    conflict_markers = task.get("conflict_markers", [])
    found_conflicts = [marker for marker in conflict_markers if marker in combined]
    if found_conflicts:
        return {"task_id": task_id, "classification": "conflict", "reason": "发现与冻结边界冲突的标记。", "evidence": found_conflicts}

    expected_hashes = task.get("expected_hashes", {})
    if expected_hashes:
        exact = True
        checked: List[str] = []
        for rel_text, digest in expected_hashes.items():
            path = repository / safe_relative_path(rel_text)
            if not path.is_file() or path.is_symlink() or sha256_file(path) != digest:
                exact = False
                break
            checked.append(rel_text)
        if exact:
            return {"task_id": task_id, "classification": "satisfied", "reason": "当前实现与冻结的已知实现精确一致。", "evidence": checked}

    markers = task.get("equivalence_markers", {})
    if markers:
        matched: List[str] = []
        equivalent = True
        for rel_text, values in markers.items():
            path = repository / safe_relative_path(rel_text)
            text = _read_text_if_small(path)
            if not text or any(value not in text for value in values):
                equivalent = False
                break
            matched.append(rel_text)
        if equivalent:
            return {"task_id": task_id, "classification": "equivalent", "reason": "上游已有语义等价实现，应保留上游而不覆盖。", "evidence": matched}

    required_paths = list(task.get("required_paths", []))
    required_missing = [rel for rel in required_paths if not (repository / safe_relative_path(rel)).exists()]
    if not present or required_missing:
        return {"task_id": task_id, "classification": "apply", "reason": "目标语义尚未实现，需要新增。", "evidence": sorted(set(missing + required_missing))}
    return {"task_id": task_id, "classification": "adapt", "reason": "目标已有相关实现但非等价，应在保留上游优点的前提下适配。", "evidence": present}


def reconcile(repository: Path, spec_path: Path, output: Optional[Path] = None) -> Dict[str, Any]:
    repository = ensure_plain_directory(repository)
    spec = read_json(spec_path)
    validated = validate_semantic_spec(spec)
    results = [classify_task(repository, task) for task in validated["tasks"]]
    counts = {status: 0 for status in sorted(ALLOWED_CLASSIFICATIONS)}
    for item in results:
        status = item["classification"]
        if status not in counts:
            raise TeleiosisError("SEMANTIC_CLASSIFICATION", "产生了未知 Semantic Reconcile 分类。", {"status": status})
        counts[status] += 1
    hard_stop = counts["conflict"] > 0 or counts["blocked"] > 0
    report = {
        "schema_version": "teleiosis.semantic_reconcile_report.v5",
        "status": "BLOCKED" if hard_stop else "READY",
        "repository": str(repository),
        "spec_hash": validated["spec_hash"],
        "repository_observation": "moving-main-observation-not-freeze-point",
        "counts": counts,
        "tasks": results,
        "rules": {
            "preserve_newer_or_better_upstream": True,
            "fixed_repository_sha_gate": False,
            "whole_tree_overwrite": False,
        },
    }
    report["report_hash"] = canonical_json_hash(report)
    if output is not None:
        atomic_write_json(output, report)
    return report
