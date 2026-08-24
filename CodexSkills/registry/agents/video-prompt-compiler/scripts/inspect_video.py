#!/usr/bin/env python3
"""Create metadata, uniformly sampled frames, and a contact sheet for a video.

Requires ffmpeg and ffprobe on PATH. It intentionally performs no OCR and no
semantic analysis; a host vision model should inspect the resulting images.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path


DETAIL_COUNTS = {"fast": 5, "standard": 9, "detailed": 15}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"{name} is required but was not found on PATH")
    return path


def probe(video: Path) -> dict:
    ffprobe = require_tool("ffprobe")
    result = run([
        ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)
    ])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe failed")
    raw = json.loads(result.stdout)
    streams = raw.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration_raw = raw.get("format", {}).get("duration") or video_stream.get("duration") or 0
    try:
        duration = float(duration_raw)
    except (TypeError, ValueError):
        duration = 0.0

    def fps_value(value: str | None) -> float | None:
        if not value or value == "0/0":
            return None
        try:
            a, b = value.split("/", 1)
            return float(a) / float(b)
        except (ValueError, ZeroDivisionError):
            return None

    return {
        "source_name": video.name,
        "duration_seconds": round(duration, 3),
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "fps": fps_value(video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate")),
        "video_codec": video_stream.get("codec_name"),
        "audio_present": audio_stream is not None,
        "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
        "sample_aspect_ratio": video_stream.get("sample_aspect_ratio"),
        "display_aspect_ratio": video_stream.get("display_aspect_ratio"),
        "semantic_analysis": "NOT_PERFORMED",
        "ocr": "NOT_PERFORMED",
    }


def timestamps(duration: float, count: int) -> list[float]:
    if duration <= 0:
        return [0.0]
    if count == 1:
        return [duration / 2]
    margin = min(0.15, duration * 0.01)
    start = margin
    end = max(start, duration - margin)
    step = (end - start) / (count - 1)
    return [round(start + i * step, 3) for i in range(count)]


def extract_frame(ffmpeg: str, video: Path, ts: float, output: Path, width: int) -> None:
    result = run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-ss", f"{ts:.3f}", "-i", str(video),
        "-frames:v", "1", "-vf", f"scale={width}:-2", "-q:v", "2", "-y", str(output)
    ])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"failed to extract frame at {ts}")


def contact_sheet(ffmpeg: str, video: Path, duration: float, count: int, output: Path, width: int) -> None:
    cols = 3 if count <= 9 else 4
    rows = math.ceil(count / cols)
    fps = count / max(duration, 0.001)
    vf = f"fps={fps:.8f},scale={width}:-2,tile={cols}x{rows}:padding=8:margin=8"
    result = run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(video), "-vf", vf,
        "-frames:v", "1", "-q:v", "2", "-y", str(output)
    ])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "failed to create contact sheet")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract metadata, key frames and a contact sheet from a local video.")
    parser.add_argument("video", type=Path)
    parser.add_argument("--detail", choices=sorted(DETAIL_COUNTS), default="standard")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frame-width", type=int, default=480)
    args = parser.parse_args()

    if not args.video.is_file():
        print(f"ERROR: video not found: {args.video}", file=sys.stderr)
        return 2
    if args.frame_width < 160 or args.frame_width > 1920:
        print("ERROR: --frame-width must be between 160 and 1920", file=sys.stderr)
        return 2

    try:
        ffmpeg = require_tool("ffmpeg")
        metadata = probe(args.video)
        count = DETAIL_COUNTS[args.detail]
        sample_times = timestamps(float(metadata["duration_seconds"]), count)
        args.output.mkdir(parents=True, exist_ok=True)
        frame_dir = args.output / "frames"
        frame_dir.mkdir(exist_ok=True)

        frames = []
        for idx, ts in enumerate(sample_times, 1):
            target = frame_dir / f"frame_{idx:02d}_{ts:.3f}s.jpg"
            extract_frame(ffmpeg, args.video, ts, target, args.frame_width)
            frames.append({"index": idx, "timestamp_seconds": ts, "path": str(target.relative_to(args.output))})

        sheet = args.output / "contact_sheet.jpg"
        contact_sheet(ffmpeg, args.video, float(metadata["duration_seconds"]), count, sheet, min(args.frame_width, 420))
        metadata["detail"] = args.detail
        metadata["sampled_frames"] = frames
        metadata["contact_sheet"] = sheet.name
        (args.output / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "output": str(args.output), "frames": len(frames)}, ensure_ascii=False))
        return 0
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
