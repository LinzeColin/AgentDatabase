#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把选中的团队成员，从「一串人名」变成「一组被载入的视角」。

## 这个脚本存在的理由

v0.0.0.6 之前，团队路由只产出人名与一行式能力简介（team-index.json 每人约 24 条）。
而每份蒸馏产物里真正的实质——**29 条 claim、心智模型、启发式、硬边界、分歧图谱**
——从来没有进入推理。用户反馈的「路由、产出、影响结论帮助都不显著」，根因就在这里：
**团队是一份演员表，不是一组被载入的视角。**

本脚本从每位选中人物的交付 ZIP 中抽取其推理载荷，产出一份 team dossier。
**没有 dossier 就不允许团队开始推理**——这是 v0.0.0.7 的硬门。

## 输出

{
  "members": [{
     "canonical_name": ..., "subject_slug": ...,
     "mental_models": [{claim_id, claim, falsifiers, confidence}, ...],
     "heuristics":    [...],
     "hard_boundaries": [...],          # 拒答与红线，必须在回答前生效
     "refusal_template": [...],         # 族级硬性拒答
     "known_distortions": [...],        # distillation_traits 里标注的「不得写成」
     "claim_index": {claim_id: 一句话},  # 供引用时核对
  }],
  "divergences": [                       # 组内真实分歧，来自各自 divergence-map.md
     {"between": [A, B], "text": ...}
  ],
  "roster_composition": {...}            # 时效与在世构成，见 subject_status
}

用法：
    python3 build_team_dossier.py --slugs john-bogle ray-dalio george-soros
    python3 build_team_dossier.py --route-plan route-plan.json
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

RIGOROUS = {"mental-model", "heuristic", "value", "work-method", "blind-spot", "contradiction"}


def registry_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_index() -> dict[str, Any]:
    return json.loads((registry_root() / "team-index.json").read_text(encoding="utf-8"))


def find_delivery(slug: str) -> Path | None:
    """取该人物最新版本的交付 ZIP。"""
    hits = sorted(registry_root().glob(f"*/{slug}/versions/*/*.zip"))
    return hits[-1] if hits else None


def open_runtime(path: Path) -> zipfile.ZipFile:
    """交付包是嵌套的：外层是交付包，产物本体在 runtime/<slug>-persona-skill-vX.zip。

    v0.0.0.6 之前没有任何脚本读过内层，这也是「团队拿不到推理内容」的直接原因之一。
    """
    outer = zipfile.ZipFile(path)
    inner_name = next((n for n in outer.namelist() if "/runtime/" in n and n.endswith(".zip")), None)
    if inner_name is None:
        return outer
    return zipfile.ZipFile(io.BytesIO(outer.read(inner_name)))


def read_member(path: Path) -> dict[str, Any]:
    """从交付 ZIP 中抽取推理载荷。只读，不解包到磁盘。"""
    out: dict[str, Any] = {
        "mental_models": [], "heuristics": [], "values": [],
        "work_methods": [], "blind_spots": [], "contradictions": [],
        "hard_boundaries": [], "known_distortions": [], "claim_index": {},
        "divergence_text": "",
    }
    with open_runtime(path) as zf:
        names = zf.namelist()

        claims_name = next((n for n in names if n.endswith("evidence/claims.jsonl")), None)
        if claims_name:
            for line in zf.read(claims_name).decode("utf-8").splitlines():
                if not line.strip():
                    continue
                c = json.loads(line)
                cat = c.get("category")
                if cat not in RIGOROUS:
                    continue
                rec = {
                    "claim_id": c.get("claim_id"),
                    "claim": c.get("claim"),
                    "falsifiers": c.get("falsifiers", []),
                    "confidence": c.get("confidence"),
                    "time_scope": c.get("time_scope"),
                }
                bucket = {
                    "mental-model": "mental_models", "heuristic": "heuristics",
                    "value": "values", "work-method": "work_methods",
                    "blind-spot": "blind_spots", "contradiction": "contradictions",
                }[cat]
                out[bucket].append(rec)
                out["claim_index"][rec["claim_id"]] = (rec["claim"] or "")[:160]

        bnd = next((n for n in names if n.endswith("boundaries.md")), None)
        if bnd:
            text = zf.read(bnd).decode("utf-8")
            out["hard_boundaries"] = [
                ln.strip("- ").strip()
                for ln in text.splitlines()
                if ln.strip().startswith("-") and len(ln.strip()) > 8
            ]

        dvg = next((n for n in names if n.endswith("divergence-map.md")), None)
        if dvg:
            out["divergence_text"] = zf.read(dvg).decode("utf-8")

    return out


def extract_divergences(members: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """组内真实分歧：只保留「A 的分歧图谱里点名了 B」这类可核对的条目。

    这是 v0.0.0.6 完全未使用的最高价值资产——蒸馏时逐人写过的分歧，
    在组队时从未被激活。
    """
    found: list[dict[str, Any]] = []
    names = {m["canonical_name"]: m for m in members}
    for m in members:
        text = m.pop("divergence_text", "") or ""
        for other in names:
            if other == m["canonical_name"]:
                continue
            surname = other.split()[-1]
            if surname and surname in text:
                for para in re.split(r"\n\n+", text):
                    if surname in para and len(para.strip()) > 40:
                        found.append({
                            "between": sorted([m["canonical_name"], other]),
                            "stated_by": m["canonical_name"],
                            "text": para.strip()[:600],
                        })
                        break
    seen: set[tuple[str, ...]] = set()
    uniq: list[dict[str, Any]] = []
    for d in found:
        key = (tuple(d["between"]), d["text"][:80])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(d)
    return uniq


def roster_composition(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """时效构成。v0.0.0.6 的 freshness_score 用 research_cutoff——
    那是「做研究的日期」而非人物活跃度，86/91 完全相同，形同虚设。
    改用 subject_status / subject_active_through（见 backfill_subject_status.py）。
    """
    living = [c for c in cards if c.get("subject_status") == "living"]
    deceased = [c for c in cards if c.get("subject_status") == "deceased"]
    unknown = [c for c in cards if not c.get("subject_status")]
    years = [c.get("subject_active_through") for c in cards if c.get("subject_active_through")]
    return {
        "total": len(cards),
        "living": len(living),
        "deceased": len(deceased),
        "status_unknown": len(unknown),
        "active_through_range": [min(years), max(years)] if years else None,
        "warning": (
            "本组 subject_status 全部未标注，无法判断时效构成——请先运行 backfill_subject_status.py。"
            if cards and len(unknown) == len(cards) else
            "本组全部为已故人物；若任务涉及当前实践、在用工具或近三年变化，"
            "该组合的时效性不足，须显式声明或补充在世实践者。"
            if cards and not living and not unknown else None
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a team dossier: load the actual reasoning payload of selected personas.")
    ap.add_argument("--slugs", nargs="*", default=[])
    ap.add_argument("--route-plan", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    slugs = list(args.slugs)
    if args.route_plan and args.route_plan.exists():
        plan = json.loads(args.route_plan.read_text(encoding="utf-8"))
        for m in plan.get("members", plan.get("roster", [])):
            s = m.get("subject_slug") if isinstance(m, dict) else None
            if s:
                slugs.append(s)
    slugs = list(dict.fromkeys(slugs))
    if not slugs:
        print(json.dumps({"error": "no slugs given"}, ensure_ascii=False))
        return 2

    index = load_index()
    by_slug = {p["subject_slug"]: p for p in index.get("products", [])}

    members: list[dict[str, Any]] = []
    cards: list[dict[str, Any]] = []
    missing: list[str] = []
    for slug in slugs:
        card = by_slug.get(slug)
        if not card:
            missing.append(slug)
            continue
        zpath = find_delivery(slug)
        if not zpath:
            missing.append(slug)
            continue
        payload = read_member(zpath)
        payload.update({
            "canonical_name": card.get("canonical_name"),
            "subject_slug": slug,
            "identity_family_id": card.get("identity_family_id"),
            "known_distortions": card.get("distillation_traits", []),
            "refusal_template": card.get("hard_boundaries", []),
            "subject_status": card.get("subject_status"),
            "subject_active_through": card.get("subject_active_through"),
        })
        members.append(payload)
        cards.append(card)

    dossier = {
        "schema_version": "1.0",
        "members": members,
        "divergences": extract_divergences(members),
        "roster_composition": roster_composition(cards),
        "missing": missing,
        "usage_contract": {
            "must_cite": "团队中每位人物专家的每一条实质贡献，必须引用其自身 claim_index 里的 claim_id；引用不出来的贡献视为未发生。",
            "must_surface_divergence": "若 divergences 非空，最终产出必须显式呈现该分歧，不得抹平取中。",
            "must_apply_boundaries": "hard_boundaries 与 refusal_template 在回答生成前生效，不是事后过滤。",
            "must_respect_known_distortions": "known_distortions 里标注的「不得写成」是硬约束，违反即为交付失败。",
        },
    }
    text = json.dumps(dossier, ensure_ascii=False, indent=1)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(json.dumps({
            "written": str(args.output),
            "members": len(members),
            "divergences": len(dossier["divergences"]),
            "missing": missing,
            "composition": dossier["roster_composition"],
        }, ensure_ascii=False))
    else:
        print(text)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
