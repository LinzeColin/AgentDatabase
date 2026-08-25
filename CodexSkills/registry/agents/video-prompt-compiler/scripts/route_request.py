#!/usr/bin/env python3
"""Route natural-language video requests into production methods and adapters.

This helper does not generate a creative prompt. It produces a deterministic
routing contract that the host LLM uses before building the VideoPromptIR.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from model_registry import MODEL_REGISTRY, ModelRecord, resolve_model


ROUTE_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("reference_reverse", ("反推", "拆解参考", "参考视频", "复刻语法", "video to prompt", "reverse engineer", "提示词反推")),
    ("true_3d_handoff", ("cad", "blender", "有限元", "仿真", "应力场", "温度场", "流场", "真实尺寸", "可测量", "装配干涉", "精确三维")),
    ("footage_edit", ("已有素材", "原片", "素材视频", "剪辑", "混剪", "时间线", "拼接", "片段", "edl", "实拍素材")),
    ("video_extend", ("延长视频", "续写视频", "继续这个视频", "接着上一段", "extend", "continue video")),
    ("video_edit", ("改这个视频", "修改视频", "换背景", "删除视频里的", "视频转视频", "v2v", "保持原视频", "严格编辑")),
    ("image_to_video", ("让这张图动", "照片动", "图片动", "图生视频", "图片转视频", "首帧", "尾帧", "image to video", "i2v")),
    ("reference_to_video", ("动作参考", "运镜参考", "音频参考", "参考素材", "多模态参考", "reference to video", "迁移动作")),
    ("screenplay_to_shots", ("剧本转分镜", "脚本转分镜", "故事板", "storyboard", "screenplay", "逐场", "逐镜头")),
    ("prompt_optimize", ("优化这条prompt", "优化这条 prompt", "改写这条prompt", "prompt optimizer", "prompt enhancer", "提示词优化")),
    ("2d_motion_graphics", ("2d", "二维动画", "信息图", "流程动画", "图标动画", "动态图形", "motion graphics", "扁平动画")),
    ("aigc_3d_concept", ("3d", "三维", "cg", "剖面动画", "结构动画", "未来工厂", "概念三维")),
]

PRESET_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("industrial", ("工业", "设备", "工件", "焊接", "熔覆", "机加工", "车削", "磨削", "回转窑", "水泥", "钢铁", "化工", "机器人", "轴", "齿轮", "阀门")),
    ("micro_performance", ("微表情", "眼神", "呼吸", "哭", "对视", "台词", "分手", "表演", "情绪", "人物", "眨眼", "泪")),
    ("brand", ("企业宣传", "公司宣传", "品牌", "logo", "业务介绍", "供应能力", "广告", "commercial")),
    ("documentary", ("纪录", "厂区", "员工", "团队", "一天", "日常", "项目现场", "跟拍")),
    ("product", ("产品", "包装", "材质", "产品特写", "packshot", "商品")),
    ("anime", ("动漫", "二次元", "动画角色", "插画", "anime", "卡通")),
    ("2d_explainer", ("流程", "信息图", "图标", "业务地图", "2d", "二维")),
    ("3d_concept", ("3d", "cg", "剖面", "三维", "结构展示")),
]


@dataclass
class RouteResult:
    route: str
    primary_preset: str
    secondary_presets: list[str]
    target_model: str | None
    target_model_id: str | None
    target_model_status: str | None
    target_adapter: str | None
    model_candidates: list[str]
    duration_seconds: float | None
    source_duration_seconds: float | None
    aspect_ratio: str | None
    action_budget: str
    recommended_output_mode: str
    required_ir_fields: list[str]
    compiler_passes: list[str]
    selection_policy: str
    decision_reasons: list[str]
    assumptions: list[str]
    warnings: list[str]
    evidence_status: str = "ROUTING_RULES_EXECUTED"
    status: str = "ROUTED"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def contains_any(text: str, words: Iterable[str]) -> bool:
    return any(word.lower() in text for word in words)


def extract_durations(text: str, explicit_target: float | None) -> tuple[float | None, float | None]:
    """Return (target_duration, source_duration) from mixed edit/generation prose.

    Target cues such as “剪成18秒” outrank an earlier source-media length such
    as “40秒素材”. A lone duration attached to source media remains a source
    fact instead of being silently reused as the requested output length.
    """
    number = r"\d+(?:\.\d+)?"
    unit = r"(?:秒|s\b|sec(?:ond)?s?)"
    all_matches = [(float(match.group("value")), match.span("value")) for match in re.finditer(
        rf"(?P<value>{number})\s*{unit}", text, re.I
    )]

    target = explicit_target
    target_value_span: tuple[int, int] | None = None
    if target is None:
        target_patterns = (
            rf"(?:剪|裁|压缩|缩短|改|做|制作|生成|输出|导出)(?:成|为|到|出)?\s*(?P<value>{number})\s*{unit}",
            rf"(?:成片|最终|目标|交付|输出)(?:时长|长度)?\s*(?:是|为|到|:|：)?\s*(?P<value>{number})\s*{unit}",
            rf"(?:cut|edit|trim|reduce|shorten|make|export|deliver)(?:\s+\w+){{0,4}}\s+(?:to|into|at)?\s*(?P<value>{number})\s*{unit}",
            rf"(?:final|target|delivery|output)(?:\s+duration|\s+length)?\s*(?:is|to|:)?\s*(?P<value>{number})\s*{unit}",
        )
        for pattern in target_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                target = float(match.group("value"))
                target_value_span = match.span("value")
                break

    source: float | None = None
    source_value_span: tuple[int, int] | None = None
    source_patterns = (
        rf"(?P<value>{number})\s*{unit}(?:的)?(?:竖屏|横屏|原始|真实|现有|已有|实拍)?(?:素材|原片|视频|片段|footage|source video)",
        rf"(?:source|input)(?:\s+footage|\s+video)?(?:\s+duration|\s+length)?\s*(?:is|:)?\s*(?P<value>{number})\s*{unit}",
    )
    for pattern in source_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            source = float(match.group("value"))
            source_value_span = match.span("value")
            break

    if target is None:
        candidates = [(value, span) for value, span in all_matches if span != source_value_span]
        if candidates:
            target, target_value_span = candidates[-1]
        elif source is None and all_matches:
            target, target_value_span = all_matches[0]

    if source is None and len(all_matches) > 1:
        candidates = [(value, span) for value, span in all_matches if span != target_value_span]
        if candidates:
            source, source_value_span = candidates[0]

    return target, source


def extract_aspect_ratio(text: str, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    match = re.search(r"(?<!\d)(9\s*:\s*16|16\s*:\s*9|1\s*:\s*1|4\s*:\s*3|3\s*:\s*4|21\s*:\s*9)(?!\d)", text)
    if match:
        return match.group(1).replace(" ", "")
    if "竖屏" in text or "vertical" in text:
        return "9:16"
    if "横屏" in text or "widescreen" in text:
        return "16:9"
    return None


def detect_route(text: str, explicit: str | None) -> str:
    if explicit and explicit != "auto":
        return explicit
    if any(x in text for x in ("反推", "拆解参考", "复刻语法", "video to prompt", "reverse engineer", "提示词反推")) or ("拆解" in text and "参考视频" in text):
        return "reference_reverse"
    has_editable_media = any(x in text for x in (
        "素材", "原片", "实拍", "现有视频", "已有视频", "这段视频", "原视频", "视频片段", "footage", "source video"
    ))
    has_edit_intent = any(x in text for x in (
        "剪成", "剪为", "剪到", "剪出", "剪辑", "混剪", "裁剪", "拼接", "时间线", "成片", "edit footage", "cut into", "cut to", "assemble"
    ))
    if has_editable_media and has_edit_intent:
        return "footage_edit"
    if "参考" in text and "视频" in text and any(x in text for x in ("动作", "运镜", "节奏", "镜头", "风格", "声音")):
        return "reference_to_video"
    if any(x in text for x in ("图片", "照片", "产品图", "首帧")) and any(x in text for x in ("动起来", "运动", "旋转", "推近", "环绕", "图生视频")):
        return "image_to_video"
    for route, words in ROUTE_KEYWORDS:
        if contains_any(text, words):
            return route
    return "text_to_video"


def detect_presets(text: str) -> tuple[str, list[str]]:
    hits = [preset for preset, words in PRESET_KEYWORDS if contains_any(text, words)]
    if not hits:
        return "cinematic", []
    return hits[0], list(dict.fromkeys(hits[1:]))


def action_budget(duration: float | None) -> str:
    if duration is None:
        return "Default to one primary subject action, one camera behavior and one environmental response; expand only after duration is known."
    if duration <= 5:
        return "1 primary subject action + 1 camera behavior + 1 environmental response."
    if duration <= 10:
        return "1-2 continuous actions or 2 beats; require a stable end state."
    if duration <= 15:
        return "2-3 timed beats; re-anchor identity, space, light and sound across cuts."
    if duration <= 30:
        return "Use timed blocks or separate shots; do not overload one paragraph."
    return "Build a project timeline and independent shot prompts; assemble in post."


def output_mode(route: str, duration: float | None, explicit: str | None) -> str:
    if explicit and explicit != "auto":
        return explicit
    if route == "reference_reverse":
        return "reverse"
    if route in {"video_edit", "prompt_optimize"}:
        return "repair" if route == "video_edit" else "copy"
    if route in {"footage_edit", "2d_motion_graphics", "true_3d_handoff", "screenplay_to_shots"} or (duration and duration > 15):
        return "director"
    return "copy"


def candidate_ids(route: str, preset: str) -> list[str]:
    if route == "footage_edit":
        return ["minimax_design"]
    if route in {"true_3d_handoff", "2d_motion_graphics"}:
        return []
    if route in {"video_edit", "video_extend", "reference_to_video"}:
        return ["minimax_h3", "seedance_20", "kling_video_30"]
    if route == "image_to_video":
        return ["runway_gen45", "hailuo_23", "wan22"]
    if route == "reference_reverse":
        return []
    if preset == "industrial":
        return ["seedance_20", "minimax_h3", "kling_video_30"]
    if preset == "micro_performance":
        return ["kling_video_30", "minimax_h3", "veo_31"]
    if preset in {"brand", "product"}:
        return ["minimax_h3", "veo_31", "runway_gen45"]
    if preset == "anime":
        return ["wan22", "kling_video_30", "seedance_20"]
    return ["runway_gen45", "veo_31", "minimax_h3"]


def model_candidates(route: str, preset: str, explicit_model: ModelRecord | None, unverified: str | None) -> list[str]:
    if explicit_model:
        return [explicit_model.display_name]
    if unverified:
        return [f"{unverified} — VERIFY_AT_RUNTIME"]
    if route == "footage_edit":
        return ["Deterministic timeline editor / HyperFrames / FFmpeg", "MiniMax Design only if its current workspace supports the required edit operation"]
    if route == "true_3d_handoff":
        return ["Blender/CAD/engineering simulation Agent"]
    if route == "2d_motion_graphics":
        return ["HyperFrames / motion-graphics editor", "MiniMax Design for assets, not for baked-in dense text"]
    if route == "reference_reverse":
        return ["Host vision model + selected target-model adapter"]
    return [MODEL_REGISTRY[model_id].display_name for model_id in candidate_ids(route, preset)]


def required_ir_fields(route: str, preset: str) -> list[str]:
    common = ["constraint_ledger", "subject_anchor", "visible_action", "camera", "environment_light", "timeline", "audio", "end_state", "invariants"]
    mapping: dict[str, list[str]] = {
        "footage_edit": ["constraint_ledger", "asset_roles", "source_timecodes", "timeline_positions", "crop", "transitions", "captions", "audio", "do_not_generate"],
        "image_to_video": ["constraint_ledger", "preserve_from_image", "subject_motion", "camera_motion", "environment_motion", "end_state"],
        "reference_to_video": ["constraint_ledger", "reference_roles", "retention_policy", "target_scene", "timeline", "continuity", "audio", "end_state"],
        "video_edit": ["constraint_ledger", "target_video", "preserve", "change_only", "time_and_location", "forbidden_changes"],
        "video_extend": ["constraint_ledger", "last_confirmed_state", "continuity", "new_single_event", "new_end_state"],
        "screenplay_to_shots": ["constraint_ledger", "scene_objectives", "character_bible", "shot_list", "continuity_memory", "per_shot_prompt"],
        "prompt_optimize": ["constraint_ledger", "source_prompt", "precision_candidate", "expressive_candidate", "scorecard", "selected_prompt"],
        "2d_motion_graphics": ["constraint_ledger", "information_hierarchy", "objects", "layout", "animation_order", "editable_text", "timing", "brand"],
        "aigc_3d_concept": ["constraint_ledger", "geometry", "material", "camera", "light", "animation", "end_state", "concept_disclaimer"],
        "true_3d_handoff": ["constraint_ledger", "drawings_dimensions", "coordinate_system", "assembly", "motion", "camera_render", "technical_acceptance"],
        "reference_reverse": ["constraint_ledger", "global_lock", "shot_timing", "motion", "camera", "light", "audio", "end_state", "transferable_grammar"],
    }
    fields = mapping.get(route, common)
    if preset == "industrial":
        fields += ["physics_ledger", "workpiece_tool_relationship", "evidence_boundary"]
    elif preset == "micro_performance":
        fields += ["trigger", "breath", "gaze", "micro_expression", "body_weight", "reaction_timing"]
    return list(dict.fromkeys(fields))


def route_request(text: str, explicit_route: str | None = "auto", model: str | None = None,
                  duration: float | None = None, explicit_output: str | None = "auto",
                  aspect_ratio: str | None = None) -> RouteResult:
    normalized = normalize(text)
    route = detect_route(normalized, explicit_route)
    preset, secondary = detect_presets(normalized)
    duration, source_duration = extract_durations(normalized, duration)
    aspect_ratio = extract_aspect_ratio(normalized, aspect_ratio)
    record, unverified = resolve_model(model)
    warnings: list[str] = []
    assumptions: list[str] = []
    reasons = [f"Detected production method: {route}", f"Primary expression preset: {preset}"]
    if source_duration is not None and duration is not None:
        reasons.append(f"Parsed source duration {source_duration:g}s and target duration {duration:g}s separately")

    if record:
        reasons.append(f"Resolved target model to verified registry entry: {record.display_name}")
        if record.status == "RETIRED_NON_DEFAULT":
            warnings.append(f"{record.display_name} is marked RETIRED_NON_DEFAULT; choose an active adapter unless the current product surface proves availability.")
        elif record.status == "PLATFORM_VERIFY_AT_RUNTIME":
            warnings.append(f"{record.display_name} is a platform surface; enabled models, controls and costs must be checked in the user's account.")
    elif unverified:
        warnings.append(f"Target label '{unverified}' is not a verified registry entry; keep it as VERIFY_AT_RUNTIME and do not infer capabilities from the name.")

    if route == "text_to_video" and any(k in normalized for k in ("素材", "视频", "图片")):
        warnings.append("Assets are mentioned without a stable role; inspect and assign each asset before rendering a T2V prompt.")
    if route == "true_3d_handoff":
        warnings.append("AIGC 3D-looking footage cannot be presented as measurable CAD or engineering simulation.")
    if preset == "industrial":
        warnings.append("Unverified material, temperature, hardness, precision, service-life, customer or savings claims remain UNKNOWN.")
    if duration is None:
        assumptions.append("Duration is missing; use the shortest duration that can show the main action and stable ending.")
    if aspect_ratio is None:
        assumptions.append("Aspect ratio is missing; keep it as an external interface parameter until the delivery surface is known.")

    return RouteResult(
        route=route,
        primary_preset=preset,
        secondary_presets=secondary,
        target_model=record.display_name if record else unverified,
        target_model_id=record.model_id if record else None,
        target_model_status=record.status if record else "VERIFY_AT_RUNTIME" if unverified else None,
        target_adapter=record.adapter_path if record else "references/models/retired-and-unknown.md" if unverified else None,
        model_candidates=model_candidates(route, preset, record, unverified),
        duration_seconds=duration,
        source_duration_seconds=source_duration,
        aspect_ratio=aspect_ratio,
        action_budget=action_budget(duration),
        recommended_output_mode=output_mode(route, duration, explicit_output),
        required_ir_fields=required_ir_fields(route, preset),
        compiler_passes=[
            "constraint_ledger",
            "production_method_route",
            "VideoPromptIR_build",
            "precision_candidate",
            "expressive_candidate",
            "weighted_selection_with_hard_gates",
            "model_specific_render",
            "structural_validation"
        ],
        selection_policy="Select the higher-scoring candidate only after all hard constraints and route-specific gates pass; keep native-model evidence separate.",
        decision_reasons=reasons,
        assumptions=assumptions,
        warnings=warnings,
    )


def to_markdown(result: RouteResult) -> str:
    lines = [
        "# Video Prompt Compiler Route", "",
        f"- status: `{result.status}`",
        f"- route: `{result.route}`",
        f"- primary preset: `{result.primary_preset}`",
        f"- target model: `{result.target_model or 'auto'}`",
        f"- model status: `{result.target_model_status or 'auto'}`",
        f"- adapter: `{result.target_adapter or 'select after routing'}`",
        f"- target duration: `{result.duration_seconds if result.duration_seconds is not None else 'UNKNOWN'}`",
        f"- source duration: `{result.source_duration_seconds if result.source_duration_seconds is not None else 'UNKNOWN'}`",
        f"- aspect ratio: `{result.aspect_ratio or 'UNKNOWN'}`",
        f"- output mode: `{result.recommended_output_mode}`",
        f"- action budget: {result.action_budget}",
        "", "## Model candidates",
    ]
    lines.extend(f"- {item}" for item in result.model_candidates)
    lines += ["", "## Required IR fields"] + [f"- {item}" for item in result.required_ir_fields]
    lines += ["", "## Compiler passes"] + [f"- {item}" for item in result.compiler_passes]
    if result.assumptions:
        lines += ["", "## Assumptions"] + [f"- {item}" for item in result.assumptions]
    if result.warnings:
        lines += ["", "## Warnings"] + [f"- {item}" for item in result.warnings]
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Route a rough video request into a production method and model adapter.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Natural-language request")
    source.add_argument("--file", type=Path, help="UTF-8 text file containing the request")
    parser.add_argument("--route", default="auto", choices=[
        "auto", "text_to_video", "image_to_video", "reference_to_video", "video_edit", "video_extend",
        "footage_edit", "screenplay_to_shots", "prompt_optimize", "2d_motion_graphics", "aigc_3d_concept",
        "true_3d_handoff", "reference_reverse"
    ])
    parser.add_argument("--model")
    parser.add_argument("--duration", type=float)
    parser.add_argument("--aspect-ratio")
    parser.add_argument("--output-mode", default="auto", choices=["auto", "copy", "director", "reverse", "repair", "minimax"])
    parser.add_argument("--format", default="json", choices=["json", "markdown"])
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        text = args.text if args.text is not None else args.file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read input: {exc}", file=sys.stderr)
        return 2
    if not text.strip():
        print("ERROR: request is empty", file=sys.stderr)
        return 2
    result = route_request(text, args.route, args.model, args.duration, args.output_mode, args.aspect_ratio)
    rendered = json.dumps(asdict(result), ensure_ascii=False, indent=2) + "\n" if args.format == "json" else to_markdown(result)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
