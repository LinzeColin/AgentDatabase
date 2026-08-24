from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Set

from .common import TeleiosisError, canonical_json_hash, read_json

ROLE_NAMES = {
    "产品与用户价值", "软件架构与实现", "数据安全与隐私", "SRE部署与恢复", "测试验收与证据", "反证范围与阻塞"
}


def validate_ten_lenses(data: Mapping[str, Any]) -> Dict[str, Any]:
    lenses = data.get("lenses")
    if not isinstance(lenses, list) or [item.get("lens") for item in lenses if isinstance(item, dict)] != list(range(1, 11)):
        raise TeleiosisError("TEN_LENS_COVERAGE", "十视角必须精确覆盖 1—10。")
    for item in lenses:
        for field in ("new_mechanism_or_fact", "finding_delta", "changed_artifacts", "developer_burden_delta", "decision", "open_p0_p1"):
            if field not in item:
                raise TeleiosisError("TEN_LENS_FIELD", "十视角记录字段不完整。", {"lens": item.get("lens"), "field": field})
        if item["decision"] not in {"KEEP", "REVERT", "NO_CHANGE"}:
            raise TeleiosisError("TEN_LENS_DECISION", "十视角决策不合法。", {"lens": item.get("lens")})
    return {"lenses": 10, "hash": canonical_json_hash(data)}


def validate_role_round(data: Mapping[str, Any], round_number: int) -> Dict[str, Any]:
    if data.get("round") != round_number:
        raise TeleiosisError("ROLE_ROUND", "角色复审轮次不正确。", {"expected": round_number})
    if data.get("mode") not in {"isolated_subagents", "role_separated_same_model"}:
        raise TeleiosisError("ROLE_MODE", "角色复审模式不合法。")
    roles = data.get("roles")
    if not isinstance(roles, list) or {item.get("role") for item in roles if isinstance(item, dict)} != ROLE_NAMES:
        raise TeleiosisError("ROLE_COVERAGE", "六角色复审覆盖不完整。")
    for role in roles:
        for field in ("input_capsule_hash", "findings", "decision", "changed_artifacts", "developer_burden_delta"):
            if field not in role:
                raise TeleiosisError("ROLE_FIELD", "角色复审记录不完整。", {"role": role.get("role"), "field": field})
    if data.get("mode") == "role_separated_same_model" and data.get("formal_independent_pass") != "UNAVAILABLE":
        raise TeleiosisError("ROLE_INDEPENDENCE_CLAIM", "同模型角色分离不得冒充独立 PASS。")
    return {"round": round_number, "roles": 6, "mode": data["mode"], "hash": canonical_json_hash(data)}


def validate_persona_evidence(data: Mapping[str, Any]) -> Dict[str, Any]:
    status = data.get("status")
    if status == "VALID_PERSONA_TEAM_CALL":
        if not data.get("dossier_hash") or not data.get("claim_ids") or not data.get("divergences_presented"):
            raise TeleiosisError("PERSONA_DOSSIER_GATE", "人物专家团队缺少 dossier、claim_id 或真实分歧。")
        if len(set(data["claim_ids"])) != len(data["claim_ids"]):
            raise TeleiosisError("PERSONA_CLAIM_DUPLICATE", "人物专家 claim_id 重复。")
    elif status == "INSUFFICIENT_ROSTER_FALLBACK":
        if data.get("persona_contributions_counted") is not False:
            raise TeleiosisError("PERSONA_FALLBACK_CLAIM", "未载入 dossier 时不得计入人物专家贡献。")
        if data.get("fallback_mode") != "neutral_functional_roles":
            raise TeleiosisError("PERSONA_FALLBACK_MODE", "insufficient_roster 只能使用中立功能角色。")
    else:
        raise TeleiosisError("PERSONA_STATUS", "人物专家证据状态不合法。", {"status": status})
    return {"status": status, "hash": canonical_json_hash(data)}


def validate_reviews(root: Path) -> Dict[str, Any]:
    ten = validate_ten_lenses(read_json(root / "evidence/preparation/ten-lens-review.json"))
    first = validate_role_round(read_json(root / "evidence/preparation/role-review-round1.json"), 1)
    second = validate_role_round(read_json(root / "evidence/preparation/role-review-round2.json"), 2)
    persona = validate_persona_evidence(read_json(root / "evidence/preparation/persona-team-evidence.json"))
    result = {
        "schema_version": "teleiosis.review_validation.v5",
        "status": "PASS",
        "ten_lens": ten,
        "role_rounds": [first, second],
        "persona": persona,
        "formal_independent_review": "UNAVAILABLE",
    }
    result["validation_hash"] = canonical_json_hash(result)
    return result
