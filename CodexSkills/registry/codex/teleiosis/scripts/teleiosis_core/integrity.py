from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from .common import (
    PACKAGE_ROOT,
    VERSION,
    TeleiosisError,
    canonical_json_hash,
    iter_tree_files,
    read_json,
    safe_relative_path,
    sha256_file,
    tree_manifest,
)

GENESIS_SHA256 = "14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086"
REQUIRED_ROOT_FILES = {
    "SKILL.md", "README.md", "VERSION", "LICENSE", "NOTICE.md", "MANIFEST.sha256",
    "CANONICAL_STATE.json", "ACCEPTANCE_CONTRACT.json", "TASK_DAG.json", "TRACEABILITY_MATRIX.json",
    "START_HERE.py", "install.py", "ROADMAP.md", "PURSUING_GOAL.txt",
}
FORBIDDEN_RELEASE_MARKERS = ("TO" + "DO", "T" + "BD", "FIX" + "ME")
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


def parse_frontmatter(path: Path) -> Dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise TeleiosisError("FRONTMATTER_MISSING", "SKILL.md 缺少 frontmatter。")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise TeleiosisError("FRONTMATTER_INVALID", "SKILL.md frontmatter 未闭合。")
    block = text[4:end]
    values: Dict[str, str] = {}
    current_section = ""
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if ":" not in raw:
            continue
        key, value = raw.strip().split(":", 1)
        value = value.strip().strip('"').strip("'")
        if indent == 0:
            current_section = key if not value else ""
            values[key] = value
        elif current_section:
            values[current_section + "." + key] = value
    return values


def load_manifest(root: Path) -> Dict[str, Tuple[str, int]]:
    path = root / "MANIFEST.sha256"
    if not path.is_file() or path.is_symlink():
        raise TeleiosisError("MANIFEST_MISSING", "缺少 MANIFEST.sha256。")
    entries: Dict[str, Tuple[str, int]] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  ([0-9]+)  (.+)", line)
        if not match:
            raise TeleiosisError("MANIFEST_FORMAT", "Manifest 行格式不合法。", {"line": number})
        digest, size_text, rel_text = match.groups()
        rel = safe_relative_path(rel_text).as_posix()
        if rel == "MANIFEST.sha256" or rel in entries:
            raise TeleiosisError("MANIFEST_DUPLICATE", "Manifest 包含自身或重复路径。", {"path": rel})
        entries[rel] = (digest, int(size_text))
    return entries


def verify_manifest(root: Path, strict: bool = True) -> Dict[str, Any]:
    declared = load_manifest(root)
    actual: Dict[str, Tuple[str, int]] = {}
    for rel, path in iter_tree_files(root, include_manifest=False):
        actual[rel.as_posix()] = (sha256_file(path), path.stat().st_size)
    missing = sorted(set(declared) - set(actual))
    extra = sorted(set(actual) - set(declared))
    mismatched = sorted(path for path in set(declared) & set(actual) if declared[path] != actual[path])
    if missing or mismatched or (strict and extra):
        raise TeleiosisError("MANIFEST_MISMATCH", "文件清单与真实文件树不一致。", {"missing": missing, "extra": extra if strict else [], "mismatched": mismatched})
    return {"files": len(actual), "bytes": sum(size for _, size in actual.values()), "strict": strict}


def verify_version(root: Path) -> Dict[str, Any]:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    fm = parse_frontmatter(root / "SKILL.md")
    release = read_json(root / "metadata/release.json")
    values = {"VERSION": version, "SKILL": fm.get("metadata.version"), "release": release.get("version")}
    if any(value != VERSION for value in values.values()):
        raise TeleiosisError("VERSION_MISMATCH", "版本声明不一致。", values)
    if fm.get("name") != "teleiosis":
        raise TeleiosisError("SKILL_NAME_MISMATCH", "Skill 安装身份必须是 teleiosis。", {"name": fm.get("name")})
    if fm.get("metadata.architecture") != "single-skill-four-built-in-full-run-engines":
        raise TeleiosisError("ARCHITECTURE_MISMATCH", "SKILL 架构声明不正确。")
    return values


def verify_genesis(root: Path) -> Dict[str, Any]:
    lock = read_json(root / "constitution/genesis-lock.json")
    locked_path = root / lock.get("locked_path", "")
    if not locked_path.is_file() or locked_path.is_symlink():
        raise TeleiosisError("GENESIS_MISSING", "Locked Genesis 不存在。")
    actual = sha256_file(locked_path)
    if actual != GENESIS_SHA256 or lock.get("locked_sha256") != GENESIS_SHA256:
        raise TeleiosisError("GENESIS_MISMATCH", "永久 Genesis 哈希不匹配。", {"actual": actual, "expected": GENESIS_SHA256})
    effective = read_json(root / "constitution/effective-requirements.v0.0.0.5.json")
    if effective.get("effective_version") != VERSION:
        raise TeleiosisError("EFFECTIVE_GENESIS_VERSION", "有效 Genesis 版本不正确。")
    requirements = effective.get("requirements")
    if not isinstance(requirements, list):
        raise TeleiosisError("EFFECTIVE_REQUIREMENTS_INVALID", "有效需求列表不存在。")
    ids = [item.get("id") for item in requirements if isinstance(item, dict)]
    expected = ["WBI-GB-%03d" % idx for idx in range(1, 43)]
    if ids != expected:
        raise TeleiosisError("REQUIREMENT_ID_GAP", "WBI-GB-001—042 必须连续、唯一且有序。", {"ids": ids})
    amendments = effective.get("amendments", [])
    for item in amendments:
        rel = safe_relative_path(item["path"])
        path = root / rel
        if sha256_file(path) != item.get("sha256"):
            raise TeleiosisError("AMENDMENT_MISMATCH", "Amendment 哈希不匹配。", {"path": rel.as_posix()})
    composite_payload = dict(effective)
    expected_composite = composite_payload.pop("effective_composite_sha256", None)
    actual_composite = canonical_json_hash(composite_payload)
    if expected_composite != actual_composite:
        raise TeleiosisError("COMPOSITE_MISMATCH", "有效 Genesis composite hash 不匹配。")
    return {"locked_sha256": actual, "requirements": len(ids), "effective_composite_sha256": actual_composite}


def verify_json_files(root: Path) -> Dict[str, Any]:
    count = 0
    for rel, path in iter_tree_files(root, include_manifest=True):
        if path.suffix.lower() not in {".json"}:
            continue
        read_json(path)
        count += 1
    return {"json_files": count}


def verify_capabilities(root: Path) -> Dict[str, Any]:
    suite = read_json(root / "metadata/capability-manifest.json")
    modules = suite.get("modules")
    if not isinstance(modules, list) or [item.get("symbol") for item in modules] != ["T", "S", "P", "A"]:
        raise TeleiosisError("MODULE_SET_INVALID", "四个模块必须按 T/S/P/A 声明。")
    all_ids: Set[str] = set()
    counts = {}
    for item in modules:
        path = root / item["path"]
        manifest = read_json(path)
        capabilities = manifest.get("capabilities")
        if not isinstance(capabilities, list) or not capabilities:
            raise TeleiosisError("CAPABILITY_EMPTY", "模块能力表不能为空。", {"module": item.get("symbol")})
        ids = [cap.get("id") for cap in capabilities if isinstance(cap, dict)]
        if len(ids) != len(set(ids)) or any(cap_id in all_ids for cap_id in ids):
            raise TeleiosisError("CAPABILITY_DUPLICATE", "能力 ID 必须全局唯一。", {"module": item.get("symbol")})
        if any(cap.get("mandatory") is not True for cap in capabilities):
            raise TeleiosisError("CAPABILITY_NOT_MANDATORY", "正式能力表不得包含可静默跳过项。", {"module": item.get("symbol")})
        all_ids.update(ids)
        counts[item["symbol"]] = len(ids)
    if suite.get("total_capabilities_per_round") != len(all_ids):
        raise TeleiosisError("CAPABILITY_TOTAL_MISMATCH", "总能力数与模块文件不一致。")
    return {"modules": counts, "total": len(all_ids)}


def verify_dag(root: Path) -> Dict[str, Any]:
    dag = read_json(root / "TASK_DAG.json")
    tasks = dag.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise TeleiosisError("DAG_EMPTY", "任务 DAG 为空。")
    by_id = {task.get("id"): task for task in tasks if isinstance(task, dict)}
    if len(by_id) != len(tasks) or None in by_id:
        raise TeleiosisError("DAG_DUPLICATE", "任务 ID 缺失或重复。")
    required_fields = {"input", "output", "dependencies", "implementation_steps", "acceptance", "oracle", "test", "threshold", "evidence", "risk", "rollback", "stop_condition"}
    allowed_categories = {"implementation", "testing", "remediation", "review", "research", "release"}
    categories: Set[str] = set()
    for task_id, task in by_id.items():
        missing_fields = sorted(required_fields - set(task))
        if missing_fields:
            raise TeleiosisError("DAG_TASK_INCOMPLETE", "任务缺少完整执行合同字段。", {"task": task_id, "missing": missing_fields})
        if task.get("category") not in allowed_categories:
            raise TeleiosisError("DAG_CATEGORY_INVALID", "任务类别不在冻结六类中。", {"task": task_id, "category": task.get("category")})
        categories.add(task["category"])
        deps = task.get("dependencies")
        if not isinstance(deps, list) or any(dep not in by_id for dep in deps):
            raise TeleiosisError("DAG_DEPENDENCY", "任务依赖缺失。", {"task": task_id, "dependencies": deps})
        steps = task.get("implementation_steps")
        if not isinstance(steps, list) or not steps or any(not isinstance(step, str) or not step.strip() for step in steps):
            raise TeleiosisError("DAG_STEPS_INVALID", "任务实施步骤为空或无效。", {"task": task_id})
        for field in ("input", "output", "acceptance", "oracle", "test", "threshold", "evidence", "risk", "rollback", "stop_condition"):
            if not isinstance(task.get(field), str) or not task[field].strip():
                raise TeleiosisError("DAG_FIELD_EMPTY", "任务执行合同字段为空。", {"task": task_id, "field": field})
        for field in ("output", "evidence"):
            rel = safe_relative_path(task[field])
            path = root / rel
            if not path.exists() or path.is_symlink():
                raise TeleiosisError("DAG_ARTIFACT_MISSING", "任务引用的输出或证据不存在。", {"task": task_id, "field": field, "path": task[field]})
    if categories != allowed_categories:
        raise TeleiosisError("DAG_CATEGORY_COVERAGE", "任务 DAG 未覆盖冻结的六类工作。", {"missing": sorted(allowed_categories - categories), "extra": sorted(categories - allowed_categories)})
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
    constraints = dag.get("constraints", {})
    if constraints.get("real_time_wait_nodes") != 0 or constraints.get("duplicate_approval_nodes") != 0:
        raise TeleiosisError("DAG_WAIT_OR_DUPLICATE_GATE", "DAG 不得包含真实等待或重复审批。")
    return {"tasks": len(tasks), "acyclic": True, "categories": sorted(categories), "full_contract": True}


def verify_traceability(root: Path) -> Dict[str, Any]:
    acceptance = read_json(root / "ACCEPTANCE_CONTRACT.json")
    trace = read_json(root / "TRACEABILITY_MATRIX.json")
    dag = read_json(root / "TASK_DAG.json")
    valid_task_ids = {item.get("id") for item in dag.get("tasks", []) if isinstance(item, dict)}
    criteria = {item["id"] for item in acceptance.get("criteria", [])}
    entries = trace.get("entries", [])
    mapped = {item.get("requirement_id") for item in entries if isinstance(item, dict)}
    if criteria != mapped:
        raise TeleiosisError("TRACEABILITY_GAP", "Acceptance 与 Traceability 不完整对应。", {"missing": sorted(criteria - mapped), "extra": sorted(mapped - criteria)})
    evidence_count = 0
    for entry in entries:
        task_ids = entry.get("task_ids")
        if not task_ids or not isinstance(task_ids, list) or len(task_ids) != len(set(task_ids)) or any(task_id not in valid_task_ids for task_id in task_ids):
            raise TeleiosisError("TRACE_TASK_INVALID", "Traceability 引用了缺失或重复任务。", {"id": entry.get("requirement_id"), "task_ids": task_ids})
        for artifact in entry.get("artifacts", []):
            rel = safe_relative_path(artifact[:-1] if artifact.endswith("/") else artifact)
            path = root / rel
            if not path.exists() or path.is_symlink():
                raise TeleiosisError("TRACE_ARTIFACT_MISSING", "Traceability 引用的制品不存在或不安全。", {"artifact": artifact})
        if not entry.get("test") or not entry.get("oracle") or not entry.get("evidence"):
            raise TeleiosisError("TRACE_ENTRY_INCOMPLETE", "Traceability 条目缺少任务、测试、Oracle 或证据。", {"id": entry.get("requirement_id")})
        evidence_rel = safe_relative_path(entry["evidence"])
        evidence_path = root / evidence_rel
        if not evidence_path.is_file() or evidence_path.is_symlink():
            raise TeleiosisError("TRACE_EVIDENCE_MISSING", "Traceability 引用的证据文件不存在或不安全。", {"evidence": entry["evidence"]})
        evidence_count += 1
    return {"requirements": len(criteria), "mapped": len(mapped), "evidence_files": evidence_count}


def verify_docs_and_markers(root: Path) -> Dict[str, Any]:
    required_paths = [root / name for name in REQUIRED_ROOT_FILES]
    missing = sorted(str(path.relative_to(root)) for path in required_paths if not path.exists())
    if missing:
        raise TeleiosisError("ROOT_FILE_MISSING", "根目录关键文件缺失。", {"missing": missing})
    scanned = 0
    chinese_docs = ["README.md", "INSTALL.md", "ROADMAP.md", "delivery/HANDOFF.md"]
    for rel_name in chinese_docs:
        text = (root / rel_name).read_text(encoding="utf-8")
        if not re.search(r"[\u4e00-\u9fff]", text):
            raise TeleiosisError("CHINESE_DOC_MISSING", "人类操作文档必须为中文。", {"path": rel_name})
    for rel, path in iter_tree_files(root, include_manifest=True):
        if path.suffix.lower() not in {".md", ".txt", ".py", ".json", ".mmd", ".command", ".bat"}:
            continue
        text = path.read_text(encoding="utf-8", errors="strict")
        scanned += 1
        if rel.as_posix().startswith("tests/"):
            continue
        if not rel.as_posix().startswith(("sources/", "legacy/")):
            for marker in FORBIDDEN_RELEASE_MARKERS:
                if marker in text:
                    raise TeleiosisError("UNRESOLVED_MARKER", "发现未解决的开发标记。", {"path": rel.as_posix(), "marker": marker})
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                raise TeleiosisError("POSSIBLE_SECRET", "发现疑似凭证。", {"path": rel.as_posix()})
    return {"text_files_scanned": scanned, "chinese_docs": chinese_docs}


def verify_truth_boundaries(root: Path) -> Dict[str, Any]:
    state = read_json(root / "CANONICAL_STATE.json")
    status = state.get("release_status", {})
    expected = {
        "target_registry_install": "NOT_RUN",
        "native_competitor_evidence": "NOT_CLAIMED",
        "field_validation": "PENDING",
        "formal_independent_review": "UNAVAILABLE",
    }
    for key, value in expected.items():
        if status.get(key) != value:
            raise TeleiosisError("TRUTH_BOUNDARY_MISMATCH", "证据边界被错误升级。", {"field": key, "actual": status.get(key), "expected": value})
    evidence = read_json(root / "metadata/evidence-boundaries.json")
    if evidence.get("formal_pass_authority") != "external independent verifier":
        raise TeleiosisError("VERIFIER_BOUNDARY", "正式 PASS 权限必须在外部独立 Verifier。")
    return expected



def verify_v3_lineage(root: Path) -> Dict[str, Any]:
    expected = {
        "legacy/v0.0.0.3/SKILL.md": "6585cbcfdf9c516d72d558d18151d66702fe4678fec89fcdda0e44d6ad9158fd",
        "legacy/v0.0.0.3/README.md": "45446884ad930437c1bd9eaa22410fca71c2e233549a47c8004ed716fe3b1e36",
        "legacy/v0.0.0.3/MANIFEST.sha256": "a503f9288d51fc695f28fe185a728b537ba39519c1f5fb55a099c62979d71b52",
    }
    actual = {}
    for rel_text, digest in expected.items():
        path = root / rel_text
        if not path.is_file() or path.is_symlink():
            raise TeleiosisError("V3_LINEAGE_MISSING", "v0.0.0.3 基线快照缺失。", {"path": rel_text})
        current = sha256_file(path)
        if current != digest:
            raise TeleiosisError("V3_LINEAGE_HASH", "v0.0.0.3 基线快照哈希不匹配。", {"path": rel_text, "actual": current, "expected": digest})
        actual[rel_text] = current
    lines = [line for line in (root / "legacy/v0.0.0.3/MANIFEST.sha256").read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 444:
        raise TeleiosisError("V3_MANIFEST_COUNT", "v0.0.0.3 Manifest 条目数不正确。", {"actual": len(lines), "expected": 444})
    matrix = read_json(root / "legacy/v0.0.0.3/SEMANTIC_INHERITANCE.json")
    if matrix.get("status") != "FUNCTIONAL_SUPERSET_WITH_SOURCE_BOUNDARY" or matrix.get("v3_manifest_entries") != 444:
        raise TeleiosisError("V3_INHERITANCE", "v3→v5 语义继承合同不完整。")
    return {"snapshot_hashes": actual, "manifest_entries": len(lines), "status": matrix["status"]}


def verify_preparation(root: Path) -> Dict[str, Any]:
    from .regression import validate_corpus
    from .review import validate_reviews
    from .skill_audit import validate_three_passes
    from .taskpack import fresh_builder_simulation, validate_taskpack
    return {
        "taskpack": validate_taskpack(root),
        "skill_audit": validate_three_passes(root),
        "reviews": validate_reviews(root),
        "fresh_builder": fresh_builder_simulation(root),
        "regression": validate_corpus(root / "fixtures/regression/teleiosis-v5-regression.jsonl"),
    }

def verify_release(root: Path = PACKAGE_ROOT, strict: bool = True) -> Dict[str, Any]:
    root = root.resolve()
    checks: Dict[str, Any] = {}
    checks["version"] = verify_version(root)
    checks["genesis"] = verify_genesis(root)
    checks["json"] = verify_json_files(root)
    checks["capabilities"] = verify_capabilities(root)
    checks["dag"] = verify_dag(root)
    checks["traceability"] = verify_traceability(root)
    checks["documents"] = verify_docs_and_markers(root)
    checks["truth_boundaries"] = verify_truth_boundaries(root)
    checks["v3_lineage"] = verify_v3_lineage(root)
    checks["preparation"] = verify_preparation(root)
    checks["manifest"] = verify_manifest(root, strict=strict)
    return {"status": "PASS", "version": VERSION, "root": str(root), "checks": checks}
