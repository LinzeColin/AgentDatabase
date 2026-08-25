#!/usr/bin/env python3
"""Build a typed VideoPromptIR scaffold from a natural-language request.

The scaffold preserves constraints and planning decisions. Creative prose is
filled by the host LLM under SKILL.md; this script deliberately does not invent
visual facts or claim a model-ready prompt has already been produced.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path

from route_request import route_request


def parse_asset(value: str) -> dict[str, str | None]:
    parts = value.split(":", 2)
    while len(parts) < 3:
        parts.append("")
    return {"id": parts[0], "type": parts[1] or "unknown", "role": parts[2] or None}


def extract_quoted_text(text: str) -> list[str]:
    values: list[str] = []
    for pattern in (r'“([^”]+)”', r'"([^"]+)"', r"‘([^’]+)’"):
        values.extend(re.findall(pattern, text))
    return list(dict.fromkeys(values))


def build_ir(text: str, route: str = "auto", model: str | None = None,
             duration: float | None = None, aspect_ratio: str | None = None,
             output_mode: str = "auto", assets: list[dict[str, str | None]] | None = None,
             hard_constraints: list[str] | None = None) -> dict[str, object]:
    routed = route_request(text, route, model, duration, output_mode, aspect_ratio)
    assets = assets or []
    hard_constraints = hard_constraints or []
    quoted = extract_quoted_text(text)
    locked = [text.strip()]
    if routed.target_model:
        locked.append(f"Target model label: {routed.target_model}")
    if routed.source_duration_seconds is not None:
        locked.append(f"Source media duration: {routed.source_duration_seconds:g} seconds")
    if routed.duration_seconds is not None:
        locked.append(f"Target duration: {routed.duration_seconds:g} seconds")
    if routed.aspect_ratio:
        locked.append(f"Aspect ratio: {routed.aspect_ratio}")
    locked.extend(hard_constraints)
    if quoted:
        locked.extend(f"Exact quoted content: {item}" for item in quoted)

    unknowns: list[str] = []
    if routed.duration_seconds is None:
        unknowns.append("effective_duration")
    if not routed.target_model:
        unknowns.append("target_model_or_platform")
    if routed.route in {"image_to_video", "reference_to_video", "video_edit", "video_extend", "footage_edit", "reference_reverse"} and not assets:
        unknowns.append("required_asset_roles_and_identifiers")

    return {
        "ir_version": "0.2",
        "status": "IR_SCAFFOLD",
        "source_request": text.strip(),
        "routing": asdict(routed),
        "constraint_ledger": {
            "locked_facts": locked,
            "creative_space": [
                "observable camera, lighting, material and sound details that do not alter locked facts",
                "the shortest action chain needed to reach a stable end state"
            ],
            "unknowns": unknowns,
            "forbidden": [
                "invented customer, project, measurement, performance or safety claims",
                "conflicting primary camera moves in one short shot",
                "silent alteration of exact dialogue, brand names or supplied reference roles"
            ]
        },
        "production": {
            "method": routed.route,
            "primary_preset": routed.primary_preset,
            "secondary_presets": routed.secondary_presets,
            "source_duration_seconds": routed.source_duration_seconds,
            "duration_seconds": routed.duration_seconds,
            "aspect_ratio": routed.aspect_ratio,
            "output_mode": routed.recommended_output_mode,
            "action_budget": routed.action_budget
        },
        "assets": assets,
        "scene_ir": {
            "subject_anchor": None,
            "environment": None,
            "action_beats": [],
            "camera": {"shot_size": None, "angle": None, "primary_movement": None, "viewer_effect": None},
            "lighting_material_palette": {"light_direction": None, "contrast": None, "palette": None, "material_response": None},
            "audio": {"dialogue": quoted, "foreground_sfx": [], "ambience": [], "score_policy": None},
            "timeline": [],
            "end_state": None,
            "continuity_invariants": [],
            "physics_ledger": None if routed.primary_preset != "industrial" else {
                "entities": [], "geometry_and_constraints": [], "contact_or_clearance": [],
                "energy_or_force_source": [], "trajectory": [], "material_response": [],
                "environment_response": [], "state_transitions": [], "final_invariants": []
            }
        },
        "candidate_plan": {
            "precision_branch": "minimum sufficient, literal, constraint-first candidate",
            "expressive_branch": "cinematic/experiential candidate that may add only non-conflicting observable detail",
            "selector": {
                "hard_gates_first": True,
                "dimensions": [
                    "intent_fidelity", "constraint_preservation", "method_fit", "visual_executability",
                    "shot_and_camera", "temporal_action_logic", "continuity_identity", "model_input_fit",
                    "prompt_density", "audio_dialogue", "industrial_physics", "micro_performance",
                    "reference_role_clarity", "end_state", "evidence_boundary_repairability"
                ]
            }
        },
        "model_render": {
            "target_model": routed.target_model,
            "target_model_id": routed.target_model_id,
            "status": routed.target_model_status,
            "adapter_path": routed.target_adapter,
            "interface_parameters": {
                "duration_seconds": routed.duration_seconds,
                "aspect_ratio": routed.aspect_ratio,
                "resolution": None,
                "variant_count": 1
            }
        },
        "evidence": {
            "routing": "EXECUTED",
            "structural_prompt_score": "NOT_RUN",
            "native_model_generation": "NOT_RUN",
            "human_visual_review": "NOT_RUN",
            "external_verifier": "NOT_RUN"
        }
    }


def render_markdown(ir: dict[str, object]) -> str:
    routing = ir["routing"]
    production = ir["production"]
    ledger = ir["constraint_ledger"]
    lines = [
        "# VideoPromptIR Scaffold", "",
        f"- status: `{ir['status']}`",
        f"- method: `{production['method']}`",
        f"- preset: `{production['primary_preset']}`",
        f"- target model: `{routing['target_model'] or 'auto'}`",
        f"- adapter: `{routing['target_adapter'] or 'select after model choice'}`",
        "", "## Locked facts",
    ]
    lines.extend(f"- {item}" for item in ledger["locked_facts"])
    lines += ["", "## Unknowns"] + [f"- {item}" for item in ledger["unknowns"] or ["none"]]
    lines += ["", "## Required IR fields"] + [f"- {item}" for item in routing["required_ir_fields"]]
    lines += ["", "## Candidate plan", "- Precision branch: literal and constraint-first.", "- Expressive branch: observable cinematic detail without changing facts.", "- Selection: hard gates first, then weighted score; native-model evidence remains separate."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a VideoPromptIR scaffold from natural language.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--file", type=Path)
    parser.add_argument("--route", default="auto")
    parser.add_argument("--model")
    parser.add_argument("--duration", type=float)
    parser.add_argument("--aspect-ratio")
    parser.add_argument("--output-mode", default="auto")
    parser.add_argument("--asset", action="append", default=[], help="id:type:role")
    parser.add_argument("--hard-constraint", action="append", default=[])
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        text = args.text if args.text is not None else args.file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read input: {exc}", file=sys.stderr)
        return 2
    ir = build_ir(text, args.route, args.model, args.duration, args.aspect_ratio,
                  args.output_mode, [parse_asset(value) for value in args.asset], args.hard_constraint)
    rendered = json.dumps(ir, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_markdown(ir)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
