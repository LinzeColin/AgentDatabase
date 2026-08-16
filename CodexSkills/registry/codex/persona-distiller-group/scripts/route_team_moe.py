#!/usr/bin/env python3
"""Capability-first sparse router for persona expert teams.

C/B/A contract
--------------
C: calibrated sparse routing using real outcome telemetry when the telemetry file
   has sufficient samples and acceptable calibration.
B: deterministic capability-DAG routing. This is the default stable execution
   surface and the source of C's future calibration data.
A: compatibility ranking using broad category/scenario signals. It is only used
   if the task graph cannot produce a valid B route.

There is no Solo production mode.  A low-complexity request routes to exactly one
persona expert plus the mandatory neutral control plane.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from compile_task_graph import compile_graph
from team_runtime_common import (
    MODE_LIMITS,
    clamp,
    flatten_text,
    iso_year,
    overlap_score,
    read_json,
    required_control_plane,
    tokens,
    valid_mode_size,
    write_json,
)

CATEGORY_DOMAINS: dict[str, set[str]] = {
    "软件开发师": {"software-ai", "research-education"},
    "投资资本师": {"finance-investment", "operations-product"},
    "财务合规师": {"finance-investment", "legal-policy", "engineering-industry"},
    "政治法律师": {"legal-policy", "operations-product"},
    "创业经营师": {"operations-product", "finance-investment"},
    "客户营销师": {"operations-product", "creative-design"},
    "艺术设计师": {"creative-design", "operations-product"},
    "材料建工师": {"engineering-industry", "research-education"},
    "建造采购师": {"engineering-industry", "operations-product"},
    "思想教育师": {"research-education", "operations-product"},
    "医疗护理师": {"healthcare", "research-education"},
    "农林牧渔师": {"agriculture", "engineering-industry"},
}

NEGATIVE_SCOPE_MARKERS = (
    "do not route here expecting a generally better answer",
    "plain model wins",
    "below a plain model",
    "不得路由为一般性",
    "不应被路由为一般性",
    "负值",
    "negative delta",
)

CURRENT_TERMS = {"最新", "当前", "今天", "本周", "现在", "价格", "法规", "版本", "latest", "current", "today", "price", "version"}


def default_registry_root() -> Path:
    return Path(__file__).resolve().parents[1]


def candidate_text(card: dict[str, Any]) -> str:
    return " ".join(
        flatten_text(card.get(field))
        for field in (
            "canonical_name", "registration_category", "identity_family_id",
            "application_scenarios", "key_capabilities", "user_value",
            "distillation_traits", "selection_reasons", "hard_boundaries",
        )
    )


def load_admission(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "expert-fleet-admission.json"
    if not path.is_file():
        return {}
    data = read_json(path)
    return {row["subject_slug"]: row for row in data.get("experts", []) if row.get("subject_slug")}


def load_telemetry(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {"eligible_for_c": False, "reason": "telemetry unavailable; C requires >=60 outcomes, ECE<=0.12 and task-slice coverage>=0.75"}
    data = read_json(path)
    sample_count = int(data.get("sample_count", 0))
    calibration_error = float(data.get("expected_calibration_error", 1.0))
    outcome_coverage = float(data.get("task_slice_coverage", 0.0))
    data["eligible_for_c"] = sample_count >= 60 and calibration_error <= 0.12 and outcome_coverage >= 0.75
    if not data["eligible_for_c"]:
        data["reason"] = "C requires >=60 outcomes, ECE<=0.12 and task-slice coverage>=0.75"
    return data


def calibration_prior(slug: str, task_domains: list[str], telemetry: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    rows = telemetry.get("experts", {}) if telemetry.get("eligible_for_c") else {}
    row = rows.get(slug, {}) if isinstance(rows, dict) else {}
    samples = int(row.get("sample_count", 0))
    if samples < 5:
        return 0.0, {"samples": samples, "reason": "insufficient expert telemetry"}
    slice_scores = row.get("domain_scores", {}) if isinstance(row.get("domain_scores"), dict) else {}
    values = [float(slice_scores[d]) for d in task_domains if d in slice_scores]
    score = sum(values) / len(values) if values else float(row.get("overall_delta", 0.0))
    return clamp(score / 100.0, -0.25, 0.25), {"samples": samples, "source": "outcome telemetry", "raw_score": score}


def score_candidate(
    card: dict[str, Any],
    graph: dict[str, Any],
    strategy: str,
    telemetry: dict[str, Any],
    admission: dict[str, dict[str, Any]],
) -> tuple[float, dict[str, Any], str | None]:
    slug = card.get("subject_slug")
    if card.get("readiness") != "ready":
        return 0.0, {}, "readiness is not ready"
    if not slug:
        return 0.0, {}, "missing subject_slug"
    if not card.get("key_capabilities"):
        return 0.0, {}, "missing key_capabilities"

    gate = admission.get(slug, {})
    if gate.get("admission") == "blocked":
        return 0.0, {}, "blocked by expert-fleet admission gate"

    task = graph["task"]
    profile = graph["profile"]
    domains = profile["domains"]
    text = candidate_text(card)
    task_similarity = overlap_score(task, text)
    packet_similarity = max(
        (overlap_score(packet["objective"], text) for packet in graph["work_packets"]),
        default=0.0,
    )
    category_domains = CATEGORY_DOMAINS.get(str(card.get("registration_category")), set())
    domain_match = len(category_domains.intersection(domains)) / max(1, len(set(domains)))

    scenarios = overlap_score(task, card.get("application_scenarios"))
    capabilities = overlap_score(task, card.get("key_capabilities"))
    user_value = overlap_score(task, card.get("user_value"))
    evidence = 1.0 if card.get("latest_artifact") and card.get("team_card") else 0.45
    boundary = 1.0 if card.get("hard_boundaries") else 0.4

    current_task = bool(tokens(task) & CURRENT_TERMS) or float(profile.get("currentness", 0)) >= 0.35
    status = card.get("subject_status")
    active_year = card.get("subject_active_through")
    if current_task and status == "deceased":
        currentness = 0.20
    elif current_task and status == "living":
        currentness = 0.85
    elif active_year and isinstance(active_year, int) and active_year >= date.today().year - 3:
        currentness = 0.75
    else:
        currentness = 0.55

    measured_scope_text = flatten_text(card.get("user_value")).casefold()
    general_delta_penalty = 0.16 if any(marker in measured_scope_text for marker in NEGATIVE_SCOPE_MARKERS) else 0.0
    restriction_penalty = 0.08 if gate.get("admission") == "restricted" else 0.0

    prior, prior_meta = calibration_prior(slug, domains, telemetry) if strategy == "C" else (0.0, {"reason": "not C"})
    weights = {
        "task_similarity": 0.24,
        "packet_similarity": 0.15,
        "domain_match": 0.15,
        "scenario_match": 0.10,
        "capability_match": 0.14,
        "user_value_match": 0.07,
        "evidence": 0.05,
        "boundary": 0.04,
        "currentness": 0.06,
    }
    values = {
        "task_similarity": task_similarity,
        "packet_similarity": packet_similarity,
        "domain_match": domain_match,
        "scenario_match": scenarios,
        "capability_match": capabilities,
        "user_value_match": user_value,
        "evidence": evidence,
        "boundary": boundary,
        "currentness": currentness,
    }
    base = sum(weights[key] * values[key] for key in weights)
    score = clamp(base + prior - general_delta_penalty - restriction_penalty)

    # Expert Choice: the expert declines tasks outside its demonstrated competence.
    accept_threshold = 0.13 if strategy == "A" else 0.17
    if max(task_similarity, packet_similarity, capabilities, scenarios, domain_match) < accept_threshold:
        return score, {"values": values, "prior": prior_meta}, "expert-choice compatibility below threshold"

    return score, {
        "values": {k: round(v, 4) for k, v in values.items()},
        "telemetry_prior": round(prior, 4),
        "telemetry": prior_meta,
        "penalties": {
            "measured_scope": general_delta_penalty,
            "admission_restriction": restriction_penalty,
        },
    }, None


def redundancy(left: dict[str, Any], right: dict[str, Any]) -> float:
    return overlap_score(
        [left.get("key_capabilities"), left.get("application_scenarios"), left.get("distillation_traits")],
        [right.get("key_capabilities"), right.get("application_scenarios"), right.get("distillation_traits")],
    )


def marginal_select(ranked: list[dict[str, Any]], target: int) -> list[dict[str, Any]]:
    pool = list(ranked)
    chosen: list[dict[str, Any]] = []
    categories: Counter[str] = Counter()
    while pool and len(chosen) < target:
        best_index = 0
        best_value = float("-inf")
        for index, item in enumerate(pool):
            max_redundancy = max((redundancy(item["card"], prior["card"]) for prior in chosen), default=0.0)
            category = str(item["card"].get("registration_category"))
            diversity_bonus = 0.08 if categories[category] == 0 else 0.0
            repeat_penalty = min(0.12, categories[category] * 0.025)
            value = 0.76 * item["base_score"] + diversity_bonus - 0.30 * max_redundancy - repeat_penalty
            if value > best_value:
                best_index, best_value = index, value
        pick = pool.pop(best_index)
        pick["marginal_score"] = round(clamp(best_value), 4)
        pick["selection_rank"] = len(chosen) + 1
        chosen.append(pick)
        categories[str(pick["card"].get("registration_category"))] += 1
    return chosen


def downgrade_mode(mode: str, available: int) -> tuple[str | None, int]:
    """Preserve the requested mode when valid; otherwise downgrade without Solo."""
    if mode == "swarm" and available >= 25:
        return "swarm", available
    if mode == "deep_team" and available >= 10:
        return "deep_team", min(30, available)
    if mode == "small_team" and available >= 5:
        return "small_team", min(15, available)
    if mode == "single_expert" and available >= 1:
        return "single_expert", 1
    if available >= 25:
        return "swarm", available
    if available >= 10:
        return "deep_team", min(30, available)
    if available >= 5:
        return "small_team", min(15, available)
    if available >= 1:
        return "single_expert", 1
    return None, 0


def assign_packets(chosen: list[dict[str, Any]], graph: dict[str, Any]) -> list[dict[str, Any]]:
    if not chosen:
        return []
    mode = graph["mode"]
    capacity = {
        "single_expert": max(1, len(graph["work_packets"])),
        "small_team": 3,
        "deep_team": 2,
        "swarm": 1,
    }[mode]
    load: Counter[str] = Counter()
    assignments: list[dict[str, Any]] = []
    for packet in graph["work_packets"]:
        candidates: list[tuple[float, dict[str, Any]]] = []
        for item in chosen:
            slug = item["card"]["subject_slug"]
            compatibility = overlap_score(packet["objective"], candidate_text(item["card"]))
            load_penalty = 0.08 * load[slug]
            over_capacity = load[slug] >= capacity
            score = compatibility + 0.28 * item["base_score"] - load_penalty - (0.25 if over_capacity else 0.0)
            candidates.append((score, item))
        candidates.sort(key=lambda pair: (-pair[0], pair[1]["card"]["subject_slug"]))
        owner = candidates[0][1]
        slug = owner["card"]["subject_slug"]
        load[slug] += 1
        assignments.append({
            "packet_id": packet["packet_id"],
            "owner_subject_slug": slug,
            "owner_name": owner["card"].get("canonical_name"),
            "compatibility": round(clamp(candidates[0][0]), 4),
            "capacity_after_assignment": load[slug],
        })
    return assignments


def build_route(
    task: str,
    registry_root: Path,
    requested_mode: str = "auto",
    requested_size: int | None = None,
    requested_strategy: str = "auto",
    telemetry_path: Path | None = None,
) -> dict[str, Any]:
    graph = compile_graph(task, requested_mode, requested_size)
    index = read_json(registry_root / "team-index.json")
    admission = load_admission(registry_root)
    telemetry = load_telemetry(telemetry_path)

    if requested_strategy == "auto":
        strategy = "C" if telemetry.get("eligible_for_c") else "B"
        fallback_reason = None if strategy == "C" else telemetry.get("reason", "C not calibrated")
    else:
        strategy = requested_strategy.upper()
        fallback_reason = None
        if strategy == "C" and not telemetry.get("eligible_for_c"):
            strategy = "B"
            fallback_reason = telemetry.get("reason", "C not calibrated")

    ranked: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for card in index.get("products", []):
        score, breakdown, exclusion = score_candidate(card, graph, strategy, telemetry, admission)
        item = {
            "card": card,
            "base_score": round(score, 4),
            "score_breakdown": breakdown,
        }
        if exclusion:
            excluded.append({
                "subject_slug": card.get("subject_slug"),
                "canonical_name": card.get("canonical_name"),
                "reason": exclusion,
                "base_score": round(score, 4),
            })
        else:
            ranked.append(item)
    ranked.sort(key=lambda item: (-item["base_score"], str(item["card"].get("canonical_name", "")).casefold()))

    # ── Domain-signal disclosure ────────────────────────────────────────────
    # Measured 2026-08-16 over 24 pre-registered tasks: on **54%** of them
    # `domain_match` was 0 for **every** candidate in the pool. Those tasks are
    # not routed by domain at all -- ranking silently falls through to the next
    # most discriminating component, `currentness` (how recent the persona is),
    # and on that half the routing scored **-1.7 pp against a skew-preserving
    # random draw**, i.e. *worse than picking at random*. On the half that did
    # have a domain signal it scored +5.3 pp.
    #
    # The mechanism works; it is blind more than half the time. Until this
    # commit the route plan said nothing about which half a given task landed
    # in, so a silent degradation looked identical to a confident match.
    #
    # This block is **disclosure only**: it changes no score, no ranking, no
    # selection, and no headcount. Whether a zero-signal pool should instead
    # *refuse* to route ("nobody in this roster knows this subject") is the
    # Owner's call and is deliberately NOT decided here.
    def _domain_of(item: dict[str, Any]) -> float:
        vals = (item.get("score_breakdown") or {}).get("values") or {}
        try:
            return float(vals.get("domain_match") or 0.0)
        except (TypeError, ValueError):
            return 0.0

    domain_signal_candidates = sum(1 for item in ranked if _domain_of(item) > 0.0)

    requested_target = int(graph["persona_expert_target"])
    final_mode, final_target = downgrade_mode(graph["mode"], min(len(ranked), requested_target))
    downgrade: dict[str, Any] | None = None
    if final_mode is None:
        return {
            "schema_version": "persona-team.route-plan.v2",
            "status": "insufficient_roster",
            "task_summary": task,
            "requested_mode": graph["mode"],
            "mode": None,
            "persona_expert_count": 0,
            "control_plane": required_control_plane(),
            "members": [],
            "selected_roles": required_control_plane(),
            "excluded_candidates": excluded,
            "limitations": ["No real registered persona passed readiness, capability, boundary and expert-choice gates."],
            "solo_allowed": False,
        }
    if final_mode != graph["mode"] or final_target != requested_target:
        downgrade = {
            "from_mode": graph["mode"],
            "from_target": requested_target,
            "to_mode": final_mode,
            "to_target": final_target,
            "reason": "not enough relevant admitted personas; downgraded without inventing experts",
        }
        graph["mode"] = final_mode
        graph["persona_expert_target"] = final_target

    chosen = marginal_select(ranked, final_target)
    assignments = assign_packets(chosen, graph)
    expert_rows: list[dict[str, Any]] = []
    for item in chosen:
        card = item["card"]
        expert_rows.append({
            "role_id": f"persona-solver-{item['selection_rank']}",
            "role_type": "persona-solver",
            "subject_uid": card.get("subject_uid"),
            "subject_slug": card.get("subject_slug"),
            "canonical_name": card.get("canonical_name"),
            "registration_category": card.get("registration_category"),
            "identity_family_id": card.get("identity_family_id"),
            "team_card": card.get("team_card"),
            "artifact": card.get("latest_artifact"),
            "readiness": card.get("readiness"),
            "subject_status": card.get("subject_status"),
            "subject_active_through": card.get("subject_active_through"),
            "research_cutoff": card.get("research_cutoff"),
            "key_capabilities": card.get("key_capabilities", []),
            "application_scenarios": card.get("application_scenarios", []),
            "hard_boundaries": card.get("hard_boundaries", []),
            "base_score": item["base_score"],
            "marginal_score": item["marginal_score"],
            "score_breakdown": item["score_breakdown"],
            "purpose": "在被载入的真实人物 claims、方法与边界内拥有一个或多个工作包。",
        })

    controls = required_control_plane()
    selected_roles = expert_rows + controls
    return {
        "schema_version": "persona-team.route-plan.v2",
        "status": "ready",
        "task_summary": task,
        "strategy": strategy,
        "strategy_fallback_reason": fallback_reason,
        "requested_mode": requested_mode,
        "mode": final_mode,
        "mode_downgrade": downgrade,
        "persona_expert_count": len(expert_rows),
        "control_role_count": len(controls),
        "total_runtime_units": len(selected_roles),
        "persona_count_excludes_controls": True,
        "solo_allowed": False,
        "members": expert_rows,
        "domain_experts": expert_rows,
        "selected_roles": selected_roles,
        "control_plane": controls,
        "task_graph": graph,
        "packet_assignments": assignments,
        "excluded_candidates": excluded,
        "routing_observability": {
            "eligible_candidates": len(ranked),
            "excluded_candidates": len(excluded),
            "registry_products": len(index.get("products", [])),
            "telemetry_eligible_for_c": bool(telemetry.get("eligible_for_c")),
            "domain_signal_candidates": domain_signal_candidates,
            "domain_signal_present": domain_signal_candidates > 0,
            "ranking_driver": ("domain_match" if domain_signal_candidates
                               else "currentness (no candidate matched this task's domain)"),
            "target_gates": {
                "overall_delta": 95,
                "ux": 95,
                "moe": 95,
                "routing": 95,
                "functionality": 95,
                "quality": 95,
                "minimum_any_dimension": 75,
            },
        },
        "separation_protocol": [
            "hypothesis-framer freezes assumptions before persona solutions",
            "persona experts receive bounded work packets and cannot review their own work",
            "counterevidence-adversary sees sealed candidate artifacts, not hidden reasoning",
            "independent-reviewer is isolated from generators and adversary",
            "decision-judge uses a predeclared rubric and cannot edit candidate evidence",
            "synthesis-lead writes only after the judge record is frozen",
        ],
        "limitations": [
            "C is used only when real outcome telemetry satisfies the calibration contract; otherwise B is explicit.",
            "Routing score is a selection signal, not proof that a persona will improve the final task result.",
        ] + ([] if domain_signal_candidates else [
            "NO DOMAIN SIGNAL: domain_match is 0 for every eligible candidate, so this "
            "team was NOT selected by subject-matter fit. Ranking fell through to "
            "`currentness` (how recent the persona is). Measured over 24 pre-registered "
            "tasks, zero-signal routing scored -1.7 pp against a skew-preserving random "
            "draw (tasks WITH a domain signal scored +5.3 pp) -- i.e. on this task the "
            "selection is not known to beat picking at random. Treat the roster below as "
            "unranked-by-domain.",
        ]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Route a task to Single Expert, Small, Deep or Swarm persona execution.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--mode", choices=["auto", *MODE_LIMITS], default="auto")
    parser.add_argument("--size", type=int)
    parser.add_argument("--strategy", choices=["auto", "c", "b", "a"], default="auto")
    parser.add_argument("--registry-root", type=Path, default=default_registry_root())
    parser.add_argument("--telemetry", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.registry_root.expanduser().resolve()
    if not (root / "team-index.json").is_file():
        parser.error(f"team-index.json not found under {root}")
    if args.mode != "auto" and args.size is not None and not valid_mode_size(args.mode, args.size):
        parser.error(f"invalid persona expert count {args.size} for {args.mode}")
    result = build_route(args.task, root, args.mode, args.size, args.strategy, args.telemetry)
    if args.output:
        write_json(args.output, result)
        print(json.dumps({
            "written": str(args.output),
            "status": result["status"],
            "mode": result.get("mode"),
            "persona_expert_count": result.get("persona_expert_count", 0),
            "strategy": result.get("strategy"),
        }, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "ready" else 3


if __name__ == "__main__":
    raise SystemExit(main())
