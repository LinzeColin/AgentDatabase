#!/usr/bin/env python3
"""Score prompt structure across transparent dimensions.

Scores estimate specification coverage only. They are not model-quality,
preference, commercial-performance, or independent-verifier scores.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path

from model_registry import resolve_model
from validate_output import active_camera_groups, has_any, validate


WEIGHTS = {
    "intent_fidelity": 10,
    "constraint_preservation": 10,
    "method_fit": 8,
    "visual_executability": 8,
    "shot_and_camera": 8,
    "temporal_action_logic": 8,
    "continuity_identity": 7,
    "model_input_fit": 8,
    "prompt_density": 6,
    "audio_dialogue": 5,
    "industrial_physics": 5,
    "micro_performance": 4,
    "reference_role_clarity": 4,
    "end_state": 4,
    "evidence_boundary_repairability": 5,
}


def clamp(value: float) -> int:
    return max(0, min(100, round(value)))


def token_set(text: str) -> set[str]:
    """Return dependency-free lexical anchors for mixed Chinese/English text.

    English uses ordinary word tokens. Chinese uses character, bigram and
    trigram anchors so a short natural-language idea can be compared with a
    longer production prompt without treating an entire sentence as one token.
    This remains a transparent lexical proxy, not a semantic-model score.
    """
    anchors: set[str] = set()
    for token in re.findall(r"[A-Za-z0-9_]+", text.lower()):
        if len(token) > 1:
            anchors.add(f"en:{token}")
    for segment in re.findall(r"[\u4e00-\u9fff]+", text):
        for char in segment:
            anchors.add(f"zh1:{char}")
        for size in (2, 3):
            for start in range(max(0, len(segment) - size + 1)):
                anchors.add(f"zh{size}:{segment[start:start + size]}")
        if len(segment) > 1:
            anchors.add(f"zhfull:{segment}")
    return anchors


def score_prompt(text: str, source_idea: str | None = None, route: str = "text_to_video",
                 preset: str = "cinematic", duration: float | None = None,
                 model: str | None = None, input_mode: str | None = None,
                 hard_constraints: list[str] | None = None) -> dict[str, object]:
    hard_constraints = hard_constraints or []
    findings = validate(text, route, preset, duration, model, input_mode, hard_constraints)
    codes = {item.code: item.level for item in findings}
    lowered = text.lower()
    scores: dict[str, int | None] = {}
    reasons: dict[str, list[str]] = {}

    if source_idea:
        source_tokens = token_set(source_idea)
        overlap = len(source_tokens & token_set(text)) / max(1, len(source_tokens))
        scores["intent_fidelity"] = clamp(45 + overlap * 55)
        reasons["intent_fidelity"] = [f"lexical anchor overlap proxy={overlap:.2f}"]
    else:
        scores["intent_fidelity"] = 70
        reasons["intent_fidelity"] = ["source idea not supplied; neutral structural prior"]

    if hard_constraints:
        preserved = sum(item in text for item in hard_constraints)
        scores["constraint_preservation"] = clamp(100 * preserved / len(hard_constraints))
        reasons["constraint_preservation"] = [f"{preserved}/{len(hard_constraints)} hard constraints found verbatim"]
    else:
        scores["constraint_preservation"] = 80
        reasons["constraint_preservation"] = ["no external hard-constraint list supplied"]

    route_errors = {
        "image_to_video": ("I2V_NO_PRESERVE",),
        "reference_to_video": ("REFERENCE_ROLE_MISSING",),
        "video_edit": ("V2V_NO_PRESERVE", "V2V_NO_DELTA"),
        "footage_edit": ("EDIT_NO_TIMECODE",),
        "true_3d_handoff": ("FAKE_ENGINEERING_RESULT",),
    }
    route_penalty = sum(codes.get(code) == "ERROR" for code in route_errors.get(route, ())) * 35
    scores["method_fit"] = clamp(92 - route_penalty)
    reasons["method_fit"] = ["route-specific mandatory fields and contradictions"]

    action_terms = len(re.findall(r"移动|转身|旋转|推近|环绕|切削|熔覆|焊接|眨眼|呼吸|moves|turns|rotates|walks|cuts|welds|blinks|breathes", lowered))
    abstract_terms = len(re.findall(r"高级感|电影感|科技感|震撼|masterpiece|8k", lowered))
    scores["visual_executability"] = clamp(55 + min(action_terms, 5) * 9 - abstract_terms * 8)
    reasons["visual_executability"] = [f"observable action markers={action_terms}", f"abstract-only markers={abstract_terms}"]

    camera_groups = active_camera_groups(text)
    camera_score = 55 + min(len(camera_groups), 1) * 35
    if "CAMERA_CONFLICT" in codes:
        camera_score -= 60
    if "CAMERA_OVERLOAD" in codes:
        camera_score -= 25
    scores["shot_and_camera"] = clamp(camera_score)
    reasons["shot_and_camera"] = [f"camera groups={camera_groups or ['unspecified']}"]

    temporal = bool(re.search(r"\d+\s*[–-]\s*\d+\s*秒|\d{1,2}:\d{2}|随后|然后|最后|after|then|finally|\[shot\s*\d+\]", lowered))
    temporal_score = 60 + (25 if temporal else 0)
    if "ACTION_BUDGET_EXCEEDED" in codes:
        temporal_score -= 50
    elif "ACTION_BUDGET_HIGH" in codes:
        temporal_score -= 20
    scores["temporal_action_logic"] = clamp(temporal_score)
    reasons["temporal_action_logic"] = ["sequence/timing markers" if temporal else "no explicit sequence/timing marker"]

    continuity_terms = has_any(text, ["保持", "保留", "不变", "一致", "锁定", "连续", "preserve", "keep", "unchanged", "consistent", "continuity"])
    scores["continuity_identity"] = 92 if continuity_terms else 58
    reasons["continuity_identity"] = ["continuity/invariant language present" if continuity_terms else "continuity language absent"]

    record, unverified = resolve_model(model)
    if unverified:
        scores["model_input_fit"] = 45
        reasons["model_input_fit"] = ["unverified model label"]
    elif record:
        mode = input_mode or route
        fit = 95 if mode in record.modes or route in record.modes else 58
        if record.status == "RETIRED_NON_DEFAULT":
            fit = min(fit, 25)
        scores["model_input_fit"] = fit
        reasons["model_input_fit"] = [f"registry status={record.status}", f"mode={mode}"]
    else:
        scores["model_input_fit"] = 70
        reasons["model_input_fit"] = ["model not selected; generic renderer"]

    words = re.findall(r"\b[\w'-]+\b", text)
    chars = len(text)
    density = 90
    if "ADJECTIVE_SOUP" in codes:
        density -= 60
    if route == "image_to_video" and len(words) > 160:
        density -= 25
    if chars > 3500:
        density -= 25
    elif chars < 30:
        density -= 25
    scores["prompt_density"] = clamp(density)
    reasons["prompt_density"] = [f"characters={chars}", f"word-like tokens={len(words)}"]

    audio = has_any(text, ["声音", "环境声", "现场声", "对白", "旁白", "音乐", "音效", "sound", "ambience", "dialogue", "voiceover", "music", "sfx", "silence"])
    scores["audio_dialogue"] = 90 if audio else 52
    reasons["audio_dialogue"] = ["audio policy present" if audio else "audio unspecified"]

    if preset == "industrial":
        industrial_penalty = sum(code in codes for code in ("INDUSTRIAL_NO_RELATION", "INDUSTRIAL_NO_INVARIANT", "INDUSTRIAL_NO_MATERIAL_RESPONSE")) * 22
        scores["industrial_physics"] = clamp(98 - industrial_penalty)
        reasons["industrial_physics"] = ["tool/workpiece, invariants and material response"]
    else:
        scores["industrial_physics"] = None
        reasons["industrial_physics"] = ["not applicable to selected preset"]

    if preset == "micro_performance":
        performance_penalty = sum(code in codes for code in ("PERFORMANCE_NO_GAZE", "PERFORMANCE_NO_BODY", "PERFORMANCE_NO_REACTION_DELAY")) * 22
        scores["micro_performance"] = clamp(96 - performance_penalty)
        reasons["micro_performance"] = ["gaze, physiology/body and reaction timing"]
    else:
        scores["micro_performance"] = None
        reasons["micro_performance"] = ["not applicable to selected preset"]

    if route == "reference_to_video" or input_mode == "full_reference":
        scores["reference_role_clarity"] = 35 if "REFERENCE_ROLE_MISSING" in codes else 95
        reasons["reference_role_clarity"] = ["explicit asset-role relationships"]
    else:
        scores["reference_role_clarity"] = None
        reasons["reference_role_clarity"] = ["not applicable to selected route"]

    scores["end_state"] = 52 if "NO_END_STATE" in codes else 95
    reasons["end_state"] = ["stable ending detected" if "NO_END_STATE" not in codes else "stable ending absent"]

    evidence_boundary = has_any(text, ["unknown", "未验证", "概念示意", "不得改变", "只修改", "保留", "fallback", "回退", "evidence"])
    unsupported = "UNSUPPORTED_INDUSTRIAL_CLAIM" in codes
    scores["evidence_boundary_repairability"] = clamp(90 if evidence_boundary and not unsupported else 60 if not unsupported else 20)
    reasons["evidence_boundary_repairability"] = ["evidence/keep/change/fallback language"]

    applicable_weights = {name: WEIGHTS[name] for name, value in scores.items() if value is not None}
    total_weight = sum(applicable_weights.values())
    weighted = sum(float(scores[name]) * weight for name, weight in applicable_weights.items()) / total_weight
    hard_errors = [asdict(item) for item in findings if item.level == "ERROR"]
    status = "BLOCKED_BY_HARD_GATE" if hard_errors else "READY_FOR_MODEL_TEST" if weighted >= 80 else "REVISE_BEFORE_MODEL_TEST"
    return {
        "status": status,
        "overall_structural_score_percent": round(weighted, 1),
        "scope": "STRUCTURAL_SPECIFICATION_COVERAGE_ONLY",
        "native_model_evidence": "NOT_RUN",
        "human_visual_review": "NOT_RUN",
        "external_verifier": "NOT_RUN",
        "weights": WEIGHTS,
        "dimensions": {name: {"score_percent": scores[name], "reasons": reasons[name]} for name in WEIGHTS},
        "hard_gate_findings": hard_errors,
        "all_findings": [asdict(item) for item in findings]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score prompt structure without claiming media-model quality.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--file", type=Path)
    parser.add_argument("--source-idea")
    parser.add_argument("--route", default="text_to_video")
    parser.add_argument("--preset", default="cinematic")
    parser.add_argument("--duration", type=float)
    parser.add_argument("--model")
    parser.add_argument("--input-mode")
    parser.add_argument("--hard-constraint", action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        text = args.text if args.text is not None else args.file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    result = score_prompt(text, args.source_idea, args.route, args.preset, args.duration, args.model, args.input_mode, args.hard_constraint)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 1 if result["status"] == "BLOCKED_BY_HARD_GATE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
