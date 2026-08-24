#!/usr/bin/env python3
"""Current model registry used by Video Prompt Compiler.

The registry separates verified model families from vendor/client labels that
must be checked at runtime. It is routing metadata, not a promise that a model
is enabled in the user's account.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class ModelRecord:
    model_id: str
    display_name: str
    status: str
    modes: tuple[str, ...]
    prompt_style: str
    adapter_path: str
    verified_on: str
    evidence: tuple[str, ...]
    notes: str = ""


MODEL_REGISTRY: dict[str, ModelRecord] = {
    "minimax_h3": ModelRecord(
        "minimax_h3", "MiniMax H3", "ACTIVE_OFFICIAL",
        ("text_to_video", "image_to_video", "reference_to_video", "video_edit", "video_extend", "full_reference"),
        "structured_multimodal_relationships",
        "references/models/minimax-h3.md", "2026-08-17",
        ("https://www.minimax.io/blog/minimax-h3", "https://huggingface.co/MiniMaxAI/MiniMax-H3"),
        "Native multimodal context and audio; H3-specific schemas are available for base and full-reference modes."
    ),
    "hailuo_23": ModelRecord(
        "hailuo_23", "MiniMax Hailuo 2.3", "ACTIVE_OFFICIAL",
        ("text_to_video", "image_to_video"),
        "concise_motion_plus_camera",
        "references/models/hailuo-2.3.md", "2026-08-17",
        ("https://platform.minimax.io/docs/release-notes/apis", "https://platform.minimax.io/docs/api-reference/video-generation-i2v"),
        "API documentation lists T2V/I2V for Hailuo 2.3 and I2V for the Fast variant."
    ),
    "seedance_20": ModelRecord(
        "seedance_20", "Seedance 2.0", "ACTIVE_OFFICIAL",
        ("text_to_video", "image_to_video", "reference_to_video", "video_edit", "video_extend"),
        "reference_roles_plus_timeline",
        "references/models/seedance-2.0.md", "2026-08-17",
        ("https://seed.bytedance.com/en/blog/official-launch-of-seedance-2-0",),
        "Four input modalities, multimodal reference/editing, joint audio-video generation and multi-shot output."
    ),
    "kling_video_30": ModelRecord(
        "kling_video_30", "Kling VIDEO 3.0", "ACTIVE_OFFICIAL",
        ("text_to_video", "image_to_video", "reference_to_video", "multi_shot", "native_audio"),
        "subject_binding_plus_performance",
        "references/models/kling-video-3.0.md", "2026-08-17",
        ("https://app.klingai.com/global/quickstart/kling-video-3-0",),
        "Use explicit element/subject binding, speaker attribution and shot transitions only when multi-shot is intended."
    ),
    "veo_31": ModelRecord(
        "veo_31", "Veo 3.1", "ACTIVE_OFFICIAL",
        ("text_to_video", "image_to_video", "native_audio"),
        "cinematography_plus_audio",
        "references/models/veo-3.1.md", "2026-08-17",
        ("https://ai.google.dev/gemini-api/docs/models/veo-3.1-generate-preview",),
        "Professional cinematic output with native synchronized audio; availability and exact controls depend on product/API surface."
    ),
    "runway_gen45": ModelRecord(
        "runway_gen45", "Runway Gen-4.5", "ACTIVE_OFFICIAL",
        ("text_to_video", "image_to_video"),
        "clear_direct_motion_description",
        "references/models/runway-gen-4.5.md", "2026-08-17",
        ("https://help.runwayml.com/hc/en-us/articles/46974685288467-Creating-with-Gen-4-5", "https://help.runwayml.com/hc/en-us/articles/48324313115155-Image-to-Video-Prompting-Guide"),
        "For I2V, the image carries composition/style; prompt primarily describes motion and temporal progression."
    ),
    "wan22": ModelRecord(
        "wan22", "Wan2.2", "ACTIVE_OPEN_OFFICIAL",
        ("text_to_video", "image_to_video", "speech_to_video", "animate"),
        "literal_chronological_description",
        "references/models/wan2.2.md", "2026-08-17",
        ("https://github.com/Wan-Video/Wan2.2",),
        "Current official open repository found during research is Wan2.2. Later vendor labels require runtime verification."
    ),
    "ltx2": ModelRecord(
        "ltx2", "LTX-2", "ACTIVE_OPEN_OFFICIAL",
        ("text_to_video", "image_to_video", "audio_video"),
        "single_chronological_paragraph",
        "references/models/ltx-2.md", "2026-08-17",
        ("https://github.com/Lightricks/LTX-2",),
        "Official guidance favors a literal chronological paragraph kept within 200 words."
    ),
    "sora2": ModelRecord(
        "sora2", "Sora 2", "RETIRED_NON_DEFAULT",
        ("text_to_video", "image_to_video"),
        "retired_adapter",
        "references/models/retired-and-unknown.md", "2026-08-17",
        ("https://help.openai.com/en/articles/20001152-what-to-know-about-the-sora-discontinuation",),
        "Sora web/app access ended on 2026-04-26; API discontinuation is scheduled for 2026-09-24. Keep non-default and verify any remaining API surface at runtime."
    ),
    "minimax_design": ModelRecord(
        "minimax_design", "MiniMax Design", "PLATFORM_VERIFY_AT_RUNTIME",
        ("project_orchestration", "footage_edit", "multi_model"),
        "project_master_prompt",
        "references/models/minimax-design.md", "2026-08-17",
        ("https://design.minimax.io",),
        "Treat as a creation workspace/router, not as a single generation model. Enabled tools and cost visibility are account-specific."
    ),
}

ALIASES: dict[str, str] = {
    "minimax design": "minimax_design",
    "minimax hub": "minimax_design",
    "h3": "minimax_h3",
    "minimax h3": "minimax_h3",
    "hailuo": "hailuo_23",
    "hailuo 2.3": "hailuo_23",
    "海螺": "hailuo_23",
    "海螺 2.3": "hailuo_23",
    "seedance": "seedance_20",
    "seedance 2": "seedance_20",
    "seedance 2.0": "seedance_20",
    "即梦 2.0": "seedance_20",
    "kling": "kling_video_30",
    "kling 3": "kling_video_30",
    "kling 3.0": "kling_video_30",
    "kling video 3.0": "kling_video_30",
    "可灵 3": "kling_video_30",
    "veo": "veo_31",
    "veo 3": "veo_31",
    "veo 3.1": "veo_31",
    "runway": "runway_gen45",
    "gen-4.5": "runway_gen45",
    "runway gen-4.5": "runway_gen45",
    "wan": "wan22",
    "wan2.2": "wan22",
    "wan 2.2": "wan22",
    "万相": "wan22",
    "ltx": "ltx2",
    "ltx-2": "ltx2",
    "sora": "sora2",
    "sora 2": "sora2",
}


def normalize_model_name(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").split())


def resolve_model(value: str | None) -> tuple[ModelRecord | None, str | None]:
    """Return a verified registry record or an unverified literal label."""
    if not value:
        return None, None
    normalized = normalize_model_name(value)
    model_id = ALIASES.get(normalized)
    if model_id:
        return MODEL_REGISTRY[model_id], None
    return None, value.strip()


def records_for(ids: Iterable[str]) -> list[ModelRecord]:
    return [MODEL_REGISTRY[model_id] for model_id in ids if model_id in MODEL_REGISTRY]


def public_registry() -> list[dict[str, object]]:
    return [asdict(record) for record in MODEL_REGISTRY.values()]
