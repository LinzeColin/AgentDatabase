#!/usr/bin/env python3
"""Deterministic structural validator for compiled video prompts.

It detects omissions and contradictions. It does not predict visual quality and
must never be reported as native-model or human-review evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from model_registry import resolve_model


CAMERA_GROUPS = {
    "static": ("锁定镜头", "固定镜头", "static camera", "locked camera"),
    "push": ("推镜", "推近", "dolly in", "push in", "zoom in"),
    "pull": ("拉镜", "拉远", "dolly out", "pull back", "zoom out"),
    "track": ("跟拍", "跟随", "横移", "tracking", "track ", "truck "),
    "orbit": ("环绕", "orbit", "arc around"),
    "pan_tilt": ("摇镜", "倾斜", "pan ", "tilt "),
    "handheld": ("手持", "handheld"),
}
ACTION_TERMS = (
    "移动", "转身", "走", "跑", "抬", "低头", "旋转", "切削", "熔覆", "焊接", "眨眼", "呼吸", "说", "后退",
    "moves", "walks", "runs", "turns", "rotates", "cuts", "welds", "blinks", "breathes", "speaks", "reaches"
)
END_TERMS = (
    "最后", "最终", "停在", "停下", "结束时", "收束", "定格", "落在", "回到稳定", "finally", "ends with", "settles", "comes to rest", "holds on"
)
ADJECTIVE_SOUP = ("高级感", "电影感", "科技感", "震撼", "大片感", "8k", "masterpiece", "cinematic masterpiece")
INDUSTRIAL_ENTITIES = ("工件", "工具", "机器人", "刀具", "焊枪", "设备", "夹具", "workpiece", "tool", "robot", "fixture")
INDUSTRIAL_INVARIANTS = ("保持不变", "固定距离", "稳定间距", "轴线", "夹持", "轨迹", "接触", "间隙", "remain unchanged", "fixed distance", "axis", "trajectory", "contact", "clearance")
INDUSTRIAL_RESPONSE = ("熔池", "切屑", "火花", "粉尘", "热影响", "材料表面", "material response", "chip", "molten pool", "debris", "dust")
AUDIO_TERMS = ("声音", "环境声", "现场声", "对白", "旁白", "音乐", "音效", "sound", "ambience", "dialogue", "voiceover", "music", "sfx")


@dataclass
class Finding:
    level: str
    code: str
    message: str


def has_any(text: str, terms: tuple[str, ...] | list[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def active_camera_groups(text: str) -> list[str]:
    lowered = text.lower()
    return [name for name, terms in CAMERA_GROUPS.items() if any(term.lower() in lowered for term in terms)]


def count_action_beats(text: str) -> int:
    lowered = text.lower()
    return sum(1 for term in ACTION_TERMS if term.lower() in lowered)


def validate(text: str, route: str = "text_to_video", preset: str = "cinematic",
             duration: float | None = None, model: str | None = None,
             input_mode: str | None = None, hard_constraints: list[str] | None = None) -> list[Finding]:
    findings: list[Finding] = []
    stripped = text.strip()
    hard_constraints = hard_constraints or []
    if not stripped:
        return [Finding("ERROR", "EMPTY_PROMPT", "Prompt is empty.")]
    if len(stripped) < 20:
        findings.append(Finding("WARNING", "VERY_SHORT", "Prompt may be too underspecified for a stable video result."))

    model_record, unverified = resolve_model(model)
    if model_record and model_record.status == "RETIRED_NON_DEFAULT":
        findings.append(Finding("ERROR", "RETIRED_MODEL", f"{model_record.display_name} is non-default/retired in this registry; verify availability or choose an active adapter."))
    if unverified:
        findings.append(Finding("WARNING", "UNVERIFIED_MODEL_LABEL", f"Model label '{unverified}' is not in the verified registry."))

    missing_constraints = [item for item in hard_constraints if item not in stripped]
    if missing_constraints:
        findings.append(Finding("ERROR", "CONSTRAINT_DROPPED", "Missing hard constraints: " + " | ".join(missing_constraints)))

    adjective_hits = sum(1 for term in ADJECTIVE_SOUP if term.lower() in stripped.lower())
    observable_hits = count_action_beats(stripped) + len(active_camera_groups(stripped))
    if adjective_hits >= 3 and observable_hits < 2:
        findings.append(Finding("ERROR", "ADJECTIVE_SOUP", "Abstract quality words are not translated into observable action, camera, light or material conditions."))

    groups = active_camera_groups(stripped)
    if "static" in groups and any(group != "static" for group in groups):
        findings.append(Finding("ERROR", "CAMERA_CONFLICT", "Static/locked camera conflicts with another primary camera movement."))
    elif len(groups) > 2:
        findings.append(Finding("WARNING", "CAMERA_OVERLOAD", f"Too many camera behaviors for one shot: {', '.join(groups)}."))

    if not has_any(stripped, ACTION_TERMS) and route not in {"footage_edit", "2d_motion_graphics", "true_3d_handoff", "reference_reverse"}:
        findings.append(Finding("ERROR", "NO_OBSERVABLE_ACTION", "No observable subject action or state change was detected."))
    if not has_any(stripped, END_TERMS) and route not in {"footage_edit", "true_3d_handoff", "reference_reverse"}:
        findings.append(Finding("WARNING", "NO_END_STATE", "Prompt lacks a stable final state or held ending composition."))

    if duration is not None:
        actions = count_action_beats(stripped)
        if duration <= 5 and actions > 4:
            findings.append(Finding("ERROR", "ACTION_BUDGET_EXCEEDED", "The requested action chain is too dense for a 3–5 second shot."))
        elif duration <= 10 and actions > 7:
            findings.append(Finding("WARNING", "ACTION_BUDGET_HIGH", "Consider splitting the action chain or using timed beats."))
        if duration > 15 and route == "text_to_video" and not re.search(r"(?:\d{1,2}:\d{2}|\d+\s*[–-]\s*\d+\s*秒|\[shot\s*\d+\])", stripped, re.I):
            findings.append(Finding("WARNING", "LONG_VIDEO_NO_TIMELINE", "Long content should use a timeline or separate shot prompts."))

    if route == "image_to_video":
        if not has_any(stripped, ("保持", "保留", "不改变", "以输入图", "preserve", "keep", "input image", "first frame")):
            findings.append(Finding("ERROR", "I2V_NO_PRESERVE", "I2V prompt does not state what the input image anchors or preserves."))
    elif route == "reference_to_video":
        if not has_any(stripped, ("图片 1", "视频 1", "音频 1", "image 1", "video 1", "audio 1", "<subject", "<picture", "参考负责", "defines", "provides")):
            findings.append(Finding("ERROR", "REFERENCE_ROLE_MISSING", "Reference-driven prompt must assign an explicit role to each asset."))
    elif route == "video_edit":
        if not has_any(stripped, ("保留", "保持", "preserve", "keep")):
            findings.append(Finding("ERROR", "V2V_NO_PRESERVE", "Video edit prompt lacks a preserve list."))
        if not has_any(stripped, ("只改变", "仅修改", "change only", "only change")):
            findings.append(Finding("ERROR", "V2V_NO_DELTA", "Video edit prompt lacks one explicit change-only instruction."))
        if not has_any(stripped, ("秒", "时间", "位置", "at ", "between", "from ")):
            findings.append(Finding("WARNING", "V2V_NO_LOCATION", "Specify when and where the edit applies."))
    elif route == "footage_edit":
        if not re.search(r"(?:\d{1,2}:\d{2}|\d{2}:\d{2}:\d{2}|素材\s*[A-Za-z0-9]|asset\s*[A-Za-z0-9])", stripped, re.I):
            findings.append(Finding("ERROR", "EDIT_NO_TIMECODE", "Footage-edit plan lacks asset identifiers or source timecodes."))
        if not has_any(stripped, ("字幕", "caption", "旁白", "voiceover", "现场声", "audio")):
            findings.append(Finding("WARNING", "EDIT_NO_AUDIO_TEXT_PLAN", "Footage edit lacks captions/voiceover/ambient-audio treatment."))
    elif route == "true_3d_handoff":
        if has_any(stripped, ("视频模型自动算出应力", "精确仿真结果", "aigc simulation result")):
            findings.append(Finding("ERROR", "FAKE_ENGINEERING_RESULT", "A video prompt cannot produce verified engineering simulation results."))

    if preset == "industrial":
        if not has_any(stripped, INDUSTRIAL_ENTITIES):
            findings.append(Finding("ERROR", "INDUSTRIAL_NO_RELATION", "Industrial prompt lacks concrete equipment/tool/workpiece entities."))
        if not has_any(stripped, INDUSTRIAL_INVARIANTS):
            findings.append(Finding("WARNING", "INDUSTRIAL_NO_INVARIANT", "Industrial prompt lacks contact, clearance, axis, trajectory or clamping invariants."))
        if not has_any(stripped, INDUSTRIAL_RESPONSE):
            findings.append(Finding("WARNING", "INDUSTRIAL_NO_MATERIAL_RESPONSE", "Industrial prompt lacks observable material/environment response."))
        if has_any(stripped, ("提升100%", "绝对安全", "零故障", "客户证明", "寿命翻倍", "guaranteed", "100% improvement")) and not has_any(stripped, ("unknown", "未验证", "概念示意")):
            findings.append(Finding("ERROR", "UNSUPPORTED_INDUSTRIAL_CLAIM", "Potential performance/customer claim is presented without an evidence boundary."))
    elif preset == "micro_performance":
        if not has_any(stripped, ("视线", "眼神", "眨眼", "gaze", "eyes", "blink")):
            findings.append(Finding("WARNING", "PERFORMANCE_NO_GAZE", "Micro-performance prompt lacks gaze or eye behavior."))
        if not has_any(stripped, ("呼吸", "肩", "手指", "重心", "吞咽", "breath", "shoulder", "finger", "weight", "swallow")):
            findings.append(Finding("WARNING", "PERFORMANCE_NO_BODY", "Micro-performance prompt lacks physiological or body behavior."))
        if has_any(stripped, ("立刻哭", "瞬间崩溃", "immediately bursts into tears")) and not has_any(stripped, ("触发", "停顿", "after", "pause")):
            findings.append(Finding("WARNING", "PERFORMANCE_NO_REACTION_DELAY", "The reaction may occur before a visible trigger or pause."))

    if not has_any(stripped, AUDIO_TERMS) and route not in {"true_3d_handoff", "reference_reverse"}:
        findings.append(Finding("INFO", "AUDIO_UNSPECIFIED", "Audio is unspecified; explicitly choose ambience/SFX/dialogue/music or silence."))

    words = re.findall(r"\b[\w'-]+\b", stripped)
    if model_record and model_record.model_id == "hailuo_23" and len(stripped) > 2000:
        findings.append(Finding("ERROR", "HAILUO_PROMPT_LIMIT", "Hailuo API prompt exceeds the documented 2,000-character maximum."))
    if model_record and model_record.model_id == "ltx2" and len(words) > 200:
        findings.append(Finding("WARNING", "LTX_WORD_BUDGET", "LTX-2 official prompting guidance recommends staying within 200 words."))
    if model_record and model_record.model_id == "runway_gen45" and route == "image_to_video" and len(words) > 160:
        findings.append(Finding("WARNING", "RUNWAY_I2V_OVERDESCRIBED", "Runway I2V usually benefits from focusing on motion instead of restating the image."))

    if model_record and model_record.model_id == "minimax_h3" and input_mode == "full_reference":
        required = ("subject_definitions", "summary", "retention_analysis", "detailed_description", "overall_soundscape", "non_diegetic_music")
        missing = [field for field in required if field not in stripped]
        if missing:
            findings.append(Finding("ERROR", "H3_FULL_REFERENCE_SCHEMA", "Missing H3 full-reference fields: " + ", ".join(missing)))

    if not findings:
        findings.append(Finding("INFO", "STRUCTURE_OK", "No common structural problem was detected."))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a compiled video prompt with deterministic structural rules.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--file", type=Path)
    parser.add_argument("--route", default="text_to_video")
    parser.add_argument("--preset", default="cinematic")
    parser.add_argument("--duration", type=float)
    parser.add_argument("--model")
    parser.add_argument("--input-mode")
    parser.add_argument("--hard-constraint", action="append", default=[])
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()
    try:
        text = args.text if args.text is not None else args.file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    findings = validate(text, args.route, args.preset, args.duration, args.model, args.input_mode, args.hard_constraint)
    errors = sum(item.level == "ERROR" for item in findings)
    warnings = sum(item.level == "WARNING" for item in findings)
    result = {
        "status": "FAIL" if errors else "PASS_WITH_WARNINGS" if warnings else "PASS",
        "scope": "STRUCTURAL_ONLY",
        "native_model_evidence": "NOT_RUN",
        "errors": errors,
        "warnings": warnings,
        "findings": [asdict(item) for item in findings]
    }
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"# Structural validation: {result['status']}\n")
        for item in findings:
            print(f"- **{item.level} {item.code}** — {item.message}")
        print("\nNative-model evidence: NOT_RUN")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
