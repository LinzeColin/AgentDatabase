#!/usr/bin/env python3
"""Prepare and enforce the pre-build namesake disambiguation gate.

Authoritative-source search is performed by the orchestration layer. This
command is the deterministic boundary: it merges those candidate records with
same-name entries in the sibling canonical registry, assigns A/B/C labels,
writes the machine-readable gate result, and blocks workspace creation when
more than one candidate remains.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import atomic_write_json, read_json, utc_now

GATE_SCHEMA_VERSION = "1.0"
GROUP_INDEX = Path(__file__).resolve().parents[2] / "persona-distiller-group" / "team-index.json"


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = re.sub(r"[\s\-_·•./()（）]+", "", text)
    return text


def _labels(count: int) -> list[str]:
    labels: list[str] = []
    for number in range(count):
        value = number
        label = ""
        while True:
            label = chr(ord("A") + (value % 26)) + label
            value = value // 26 - 1
            if value < 0:
                break
        labels.append(label)
    return labels


def _string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"candidate {field} must be a non-empty string array")
    return [item.strip() for item in value]


def _sources(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise ValueError("candidate authoritative_sources must be a non-empty array")
    result: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append({"locator": item.strip()})
        elif isinstance(item, dict) and isinstance(item.get("locator"), str) and item["locator"].strip():
            result.append({str(key): str(value) for key, value in item.items() if value is not None})
        else:
            raise ValueError("each authoritative source needs a non-empty locator")
    return result


def _candidate(raw: dict[str, Any], *, registry_fallback: bool = False) -> dict[str, Any]:
    name = str(raw.get("canonical_name") or raw.get("name") or "").strip()
    if not name:
        raise ValueError("candidate canonical_name is required")
    scenarios = raw.get("application_scenarios") or raw.get("scenarios")
    capabilities = raw.get("key_capabilities") or raw.get("capabilities")
    sources = raw.get("authoritative_sources") or raw.get("sources")
    result = {
        "label": "",
        "canonical_name": name,
        "subject_uid": raw.get("subject_uid"),
        "identity_category": str(raw.get("identity_category") or raw.get("identity") or "待权威资料确认").strip(),
        "occupation_or_role": str(raw.get("occupation_or_role") or raw.get("occupation") or "待权威资料确认").strip(),
        "professional_background": str(raw.get("professional_background") or "待权威资料确认").strip(),
        "application_scenarios": _string_list(scenarios or (["按权威资料补充"] if registry_fallback else []), "application_scenarios"),
        "key_capabilities": _string_list(capabilities or (["按权威资料补充"] if registry_fallback else []), "key_capabilities"),
        "distinguishing_basis": str(raw.get("distinguishing_basis") or ("canonical registry subject_uid 与已登记产物" if registry_fallback else "")).strip(),
        "authoritative_sources": _sources(sources or ([{"locator": "canonical registry"}] if registry_fallback else [])),
        "evidence_level": str(raw.get("evidence_level") or "low").lower(),
    }
    if result["evidence_level"] not in {"low", "medium", "high"}:
        raise ValueError("candidate evidence_level must be low, medium, or high")
    if result["subject_uid"] is not None and not isinstance(result["subject_uid"], str):
        raise ValueError("candidate subject_uid must be a string or null")
    return result


def _registry_candidates(target_name: str) -> list[dict[str, Any]]:
    if not GROUP_INDEX.is_file():
        return []
    data = read_json(GROUP_INDEX, default={}) or {}
    matches = [item for item in data.get("products", []) if normalize_name(str(item.get("canonical_name", ""))) == normalize_name(target_name)]
    result: list[dict[str, Any]] = []
    for item in matches:
        result.append(_candidate({
            "canonical_name": item.get("canonical_name"),
            "subject_uid": item.get("subject_uid"),
            "identity_category": item.get("registration_category"),
            "application_scenarios": item.get("application_scenarios"),
            "key_capabilities": item.get("key_capabilities"),
            "distinguishing_basis": f"canonical registry subject_uid={item.get('subject_uid')}; artifact={item.get('latest_artifact')}",
        }, registry_fallback=True))
    return result


def _load_external(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    data = read_json(path)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("candidates"), list):
        return data["candidates"]
    raise ValueError("candidate file must be an array or an object with a candidates array")


def _merge_candidates(target_name: str, external: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw, fallback in [*[(item, False) for item in external], *[(item, True) for item in _registry_candidates(target_name)]]:
        candidate = _candidate(raw, registry_fallback=fallback)
        key = str(candidate.get("subject_uid") or normalize_name(candidate["canonical_name"]))
        if key in seen:
            continue
        seen.add(key)
        merged.append(candidate)
    return merged


def _card(candidate: dict[str, Any]) -> str:
    scenarios = "；".join(candidate["application_scenarios"])
    capabilities = "；".join(candidate["key_capabilities"])
    return (
        f"{candidate['label']}. 人物与身份：{candidate['canonical_name']}；"
        f"{candidate['identity_category']}；{candidate['occupation_or_role']}。\n"
        f"   专业背景：{candidate['professional_background']}。\n"
        f"   应用价值：场景：{scenarios}；关键能力：{capabilities}。\n"
        f"   区分依据：{candidate['distinguishing_basis']}。"
    )


def build_gate(target_name: str, external: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = _merge_candidates(target_name, external)
    for label, candidate in zip(_labels(len(candidates)), candidates):
        candidate["label"] = label
    count = len(candidates)
    resolution = "none" if count == 0 else "single" if count == 1 else "multiple"
    # ★★★ v0.0.0.150：**0 个候选不是「没有同名风险」，是「没人给我可比的东西」。**
    #   原先 count==0 → status "ready"，与「查过了、干净」**在产物里长得一模一样**。
    #   全库回查：32 份 namesake 产物里 **9 份是 0 候选却 ready**
    #   （Koch／Lister／Pasteur／Semmelweis／Fleming／Blackwell／DeBakey／Benardos／**Thomson**）。
    #   ★ Thomson 正是记忆里那次同名事故的人物：GE 总裁 Charles A. Coffin 被当成
    #     焊接发明人的署名放行——**他的同名门就是在 0 候选下报 ready 的**。
    #   护栏只比姓，本来就挡不住同姓者；再让「没喂候选」也算通过，等于这道门形同虚设。
    status = ("blocked" if count > 1
              else "unverified" if count == 0
              else "ready")
    selected = candidates[0].get("subject_uid") if count == 1 else None
    return {
        "schema_version": GATE_SCHEMA_VERSION,
        "target_name": target_name,
        "normalized_name": normalize_name(target_name),
        "status": status,
        "resolution": resolution,
        "candidate_count": count,
        "selected_subject_uid": selected,
        "generated_at": utc_now(),
        "search_scope": ["sibling canonical registry", "authoritative public sources supplied by orchestration"],
        "candidates": candidates,
        "candidate_cards": [_card(candidate) for candidate in candidates],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the pre-build namesake disambiguation gate.")
    parser.add_argument("--name", required=True)
    parser.add_argument("--candidates-file", type=Path, help="JSON array or object containing authoritative search candidates")
    parser.add_argument("--output", type=Path, help="Write the machine-readable gate result")
    args = parser.parse_args()
    try:
        gate = build_gate(args.name, _load_external(args.candidates_file))
        if args.output:
            atomic_write_json(args.output.expanduser().resolve(), gate)
        print(json.dumps(gate, ensure_ascii=False, indent=2, sort_keys=True))
        if gate["status"] == "blocked":
            print("BLOCKED_NAMESAKE_SELECTION", file=sys.stderr)
            return 3
        if gate["status"] == "unverified":
            print("UNVERIFIED_NAMESAKE_NO_CANDIDATES", file=sys.stderr)
            print("✗ **一个候选都没有——这不是「没有同名风险」，是「没核」。**",
                  file=sys.stderr)
            print("  要么用 --candidates-file 喂进权威检索结果，"
                  "要么在台账里写明为什么这个人没有可比对象。", file=sys.stderr)
            return 4
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
