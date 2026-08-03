from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Set

from .common import TeleiosisError, canonical_json_hash, read_json

PASS_ORDER = ["A", "B", "C"]
REQUIRED_CALL_FIELDS = {
    "skill", "version", "purpose", "input_subject", "input_hash", "output_artifacts",
    "findings", "new_mechanisms", "closed_risks", "developer_burden_delta", "rerun_trigger",
}
REQUIRED_COVERAGE = {
    "产品", "前端", "后端", "架构", "数据", "安全", "可靠性", "运维", "测试", "部署", "治理", "验收"
}


def validate_catalog_snapshot(data: Mapping[str, Any]) -> Dict[str, Any]:
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise TeleiosisError("CATALOG_EMPTY", "Skill Catalog snapshot 为空。")
    names: Set[str] = set()
    for item in entries:
        if not isinstance(item, dict):
            raise TeleiosisError("CATALOG_ENTRY", "Skill Catalog 条目必须是对象。")
        for field in ("name", "description", "version", "scope", "entrypoint"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise TeleiosisError("CATALOG_FIELD", "Skill Catalog 条目字段不完整。", {"field": field, "entry": item.get("name")})
        if item["name"] in names:
            raise TeleiosisError("CATALOG_DUPLICATE", "Skill Catalog 名称重复。", {"name": item["name"]})
        names.add(item["name"])
    coverage = set(data.get("coverage_domains", []))
    if not REQUIRED_COVERAGE.issubset(coverage):
        raise TeleiosisError("CATALOG_COVERAGE", "Skill Catalog 路由覆盖域不完整。", {"missing": sorted(REQUIRED_COVERAGE - coverage)})
    return {"entries": len(entries), "coverage_domains": sorted(coverage), "snapshot_hash": canonical_json_hash(data)}


def validate_pass(data: Mapping[str, Any], expected_pass: str) -> Dict[str, Any]:
    if data.get("pass") != expected_pass:
        raise TeleiosisError("SKILL_PASS_ORDER", "Skill Audit pass 顺序不正确。", {"expected": expected_pass, "actual": data.get("pass")})
    calls = data.get("calls")
    if not isinstance(calls, list) or not calls:
        raise TeleiosisError("SKILL_PASS_EMPTY", "Skill Audit pass 没有真实调用记录。", {"pass": expected_pass})
    for call in calls:
        missing = sorted(REQUIRED_CALL_FIELDS - set(call))
        if missing:
            raise TeleiosisError("SKILL_CALL_INCOMPLETE", "Skill 调用记录字段不完整。", {"pass": expected_pass, "skill": call.get("skill"), "missing": missing})
        if not call["output_artifacts"] and not call["findings"]:
            raise TeleiosisError("SKILL_CALL_NO_DELTA", "Skill 调用既无制品也无 Finding。", {"pass": expected_pass, "skill": call.get("skill")})
        burden = call["developer_burden_delta"]
        if not isinstance(burden, dict) or not any(bool(value) for value in burden.values()):
            raise TeleiosisError("SKILL_CALL_NO_BURDEN_DELTA", "Skill 调用没有实质 Developer Burden Delta。", {"pass": expected_pass, "skill": call.get("skill")})
    return {"pass": expected_pass, "calls": len(calls), "input_hash": data.get("input_hash"), "pass_hash": canonical_json_hash(data)}


def validate_three_passes(root: Path) -> Dict[str, Any]:
    snapshot = validate_catalog_snapshot(read_json(root / "metadata/skill-catalog-snapshot.json"))
    results: List[Dict[str, Any]] = []
    input_hashes: List[str] = []
    for code, filename in zip(PASS_ORDER, ["skill-pass-a.json", "skill-pass-b.json", "skill-pass-c.json"]):
        data = read_json(root / "evidence/preparation" / filename)
        result = validate_pass(data, code)
        if not isinstance(result["input_hash"], str) or len(result["input_hash"]) != 64:
            raise TeleiosisError("SKILL_PASS_INPUT_HASH", "Skill pass 缺少合法 input hash。", {"pass": code})
        input_hashes.append(result["input_hash"])
        results.append(result)
    if len(set(input_hashes)) != 3:
        raise TeleiosisError("SKILL_PASS_NO_INPUT_DELTA", "三次 Skill pass 必须对应真实变化后的不同输入。", {"hashes": input_hashes})
    summary = {
        "schema_version": "teleiosis.skill_audit_summary.v5",
        "status": "PASS",
        "catalog": snapshot,
        "passes": results,
        "formal_verifier_pass": "NOT_ISSUED",
    }
    summary["summary_hash"] = canonical_json_hash(summary)
    return summary
