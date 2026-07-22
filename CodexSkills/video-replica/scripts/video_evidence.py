#!/usr/bin/env python3
"""Deterministic evidence extraction for the video-replica skill.

The script intentionally uses only Python's standard library plus ffmpeg/ffprobe.
It preserves decoded-frame order and presentation timestamps, creates immutable
hash manifests, and keeps mutable human review state outside that manifest.
"""

from __future__ import print_function

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shlex
import shutil
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


VERSION = "2.0.0"
REQUIRED_TOOLS = ("ffmpeg", "ffprobe")
PASS_REVIEW_STATUSES = {"reviewed", "duplicate_verified"}
MUTABLE_EVIDENCE_FILES = {
    "capture_context.json",
    "FRAME_REVIEW_LEDGER.csv",
    "validation_result.json",
    "EVIDENCE_MANIFEST.sha256",
}

FRAME_FIELDS = (
    "media_type,stream_index,key_frame,pts,pts_time,best_effort_timestamp,"
    "best_effort_timestamp_time,pkt_duration,pkt_duration_time,pict_type,"
    "repeat_pict,width,height,pix_fmt,color_range,color_space,color_primaries,"
    "color_transfer,crop_top,crop_bottom,crop_left,crop_right,side_data_list"
)

SHOWINFO_RE = re.compile(
    r"\bn:\s*(?P<n>\d+).*?\bpts:\s*(?P<pts>-?\d+).*?"
    r"\bpts_time:(?P<pts_time>[-+0-9.eE]+)"
)
METADATA_FRAME_RE = re.compile(
    r"\bframe:(?P<n>\d+)\s+pts:(?P<pts>-?\d+)\s+"
    r"pts_time:(?P<pts_time>[-+0-9.eE]+)"
)
YAVG_RE = re.compile(r"lavfi\.signalstats\.YAVG=(?P<value>[-+0-9.eE]+)")


class EvidenceError(RuntimeError):
    pass


def json_write(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def run_command(command: Sequence[str], check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        list(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise EvidenceError(
            "command failed ({}): {}\n{}".format(
                result.returncode, shlex.join(list(command)), detail[-4000:]
            )
        )
    return result


def tool_path(name: str) -> Optional[str]:
    return shutil.which(name)


def tool_version(name: str) -> Optional[str]:
    path = tool_path(name)
    if not path:
        return None
    result = run_command([path, "-version"], check=False)
    line = (result.stdout or result.stderr).splitlines()
    return line[0] if line else "unknown"


def require_tools() -> Dict[str, str]:
    found = {name: tool_path(name) for name in REQUIRED_TOOLS}
    missing = [name for name, path in found.items() if not path]
    if missing:
        raise EvidenceError("missing required binaries: {}".format(", ".join(missing)))
    return {name: str(path) for name, path in found.items() if path}


def parse_number(value: Any) -> Optional[float]:
    if value is None or value == "N/A" or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_time(value: str) -> float:
    parts = value.strip().split(":")
    if not parts or len(parts) > 3:
        raise EvidenceError("invalid time: {}".format(value))
    try:
        numbers = [float(part) for part in parts]
    except ValueError as exc:
        raise EvidenceError("invalid time: {}".format(value)) from exc
    if any(number < 0 for number in numbers):
        raise EvidenceError("time must be non-negative: {}".format(value))
    if len(numbers) == 1:
        return numbers[0]
    if len(numbers) == 2:
        return numbers[0] * 60.0 + numbers[1]
    return numbers[0] * 3600.0 + numbers[1] * 60.0 + numbers[2]


def fraction_to_float(value: Any) -> Optional[float]:
    if not value or value in {"0/0", "N/A"}:
        return None
    try:
        numerator, denominator = str(value).split("/", 1)
        denominator_value = float(denominator)
        if denominator_value == 0:
            return None
        return float(numerator) / denominator_value
    except (ValueError, TypeError):
        return None


def ensure_video(path_value: str) -> Path:
    path = Path(path_value).expanduser().resolve()
    if not path.is_file():
        raise EvidenceError("video does not exist or is not a file: {}".format(path))
    return path


def prepare_new_output(path_value: str) -> Path:
    out = Path(path_value).expanduser().resolve()
    if out.exists():
        if not out.is_dir():
            raise EvidenceError("output path exists and is not a directory: {}".format(out))
        if any(out.iterdir()):
            raise EvidenceError("output directory is not empty: {}".format(out))
    out.mkdir(parents=True, exist_ok=True)
    return out


def probe_streams(video: Path, tools: Dict[str, str]) -> Dict[str, Any]:
    result = run_command(
        [
            tools["ffprobe"],
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            "-show_chapters",
            str(video),
        ]
    )
    return json.loads(result.stdout)


def probe_frames(video: Path, tools: Dict[str, str]) -> List[Dict[str, Any]]:
    result = run_command(
        [
            tools["ffprobe"],
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_frames",
            "-show_entries",
            "frame={}".format(FRAME_FIELDS),
            "-print_format",
            "json",
            str(video),
        ]
    )
    payload = json.loads(result.stdout)
    return [frame for frame in payload.get("frames", []) if frame.get("media_type") == "video"]


def frame_time(frame: Dict[str, Any]) -> Optional[float]:
    for key in ("best_effort_timestamp_time", "pts_time"):
        value = parse_number(frame.get(key))
        if value is not None:
            return value
    return None


def normalize_frames(frames: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for index, frame in enumerate(frames):
        copy = dict(frame)
        copy["_index"] = index
        copy["_time"] = frame_time(frame)
        normalized.append(copy)
    return normalized


def first_video_stream(raw: Dict[str, Any]) -> Dict[str, Any]:
    for stream in raw.get("streams", []):
        if stream.get("codec_type") == "video":
            return stream
    raise EvidenceError("ffprobe did not find a video stream")


def build_probe_summary(
    raw: Dict[str, Any], frames: Sequence[Dict[str, Any]], source_sha256: str
) -> Dict[str, Any]:
    video_stream = first_video_stream(raw)
    audio_streams = [
        stream for stream in raw.get("streams", []) if stream.get("codec_type") == "audio"
    ]
    times = [frame_time(frame) for frame in frames]
    numeric_times = [value for value in times if value is not None]
    deltas = [
        later - earlier
        for earlier, later in zip(numeric_times, numeric_times[1:])
        if later - earlier > 0
    ]
    duplicate_pts = sum(
        1
        for earlier, later in zip(numeric_times, numeric_times[1:])
        if later == earlier
    )
    non_monotonic_pts = sum(
        1
        for earlier, later in zip(numeric_times, numeric_times[1:])
        if later < earlier
    )

    median_delta = statistics.median(deltas) if deltas else None
    min_delta = min(deltas) if deltas else None
    max_delta = max(deltas) if deltas else None
    vfr_threshold = max(0.001, median_delta * 0.05) if median_delta else None
    vfr_suspected = bool(
        median_delta is not None
        and min_delta is not None
        and max_delta is not None
        and (max_delta - min_delta) > float(vfr_threshold)
    )

    transfer = str(video_stream.get("color_transfer") or "unknown").lower()
    pix_fmt = str(video_stream.get("pix_fmt") or "unknown").lower()
    hdr_suspected = transfer in {"smpte2084", "arib-std-b67"} or any(
        marker in pix_fmt for marker in ("p10", "p12", "10le", "12le")
    )
    duration = parse_number(raw.get("format", {}).get("duration"))
    if duration is None and numeric_times:
        last_duration = parse_number(frames[-1].get("pkt_duration_time")) or 0.0
        duration = numeric_times[-1] + last_duration - numeric_times[0]

    rotation = None
    if isinstance(video_stream.get("tags"), dict):
        rotation = video_stream["tags"].get("rotate")
    for side_data in video_stream.get("side_data_list", []) or []:
        if rotation is None and "rotation" in side_data:
            rotation = side_data.get("rotation")

    warnings = []
    if vfr_suspected:
        warnings.append("variable frame rate suspected from decoded PTS deltas")
    if duplicate_pts:
        warnings.append("duplicate presentation timestamps detected")
    if non_monotonic_pts:
        warnings.append("non-monotonic presentation timestamps detected")
    if hdr_suspected:
        warnings.append(
            "HDR/high-bit-depth signal suspected; declare player/display tone mapping before fidelity claims"
        )
    if not numeric_times:
        warnings.append("decoded frames lack usable presentation timestamps")

    return {
        "schema_version": "2.0",
        "script_version": VERSION,
        "source_sha256": source_sha256,
        "format_name": raw.get("format", {}).get("format_name"),
        "duration_seconds": duration,
        "stream_index": video_stream.get("index"),
        "codec_name": video_stream.get("codec_name"),
        "profile": video_stream.get("profile"),
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "sample_aspect_ratio": video_stream.get("sample_aspect_ratio"),
        "display_aspect_ratio": video_stream.get("display_aspect_ratio"),
        "rotation_degrees": rotation,
        "pix_fmt": video_stream.get("pix_fmt"),
        "color_range": video_stream.get("color_range"),
        "color_space": video_stream.get("color_space"),
        "color_primaries": video_stream.get("color_primaries"),
        "color_transfer": video_stream.get("color_transfer"),
        "hdr_or_high_bit_depth_suspected": hdr_suspected,
        "r_frame_rate": video_stream.get("r_frame_rate"),
        "r_frame_rate_fps": fraction_to_float(video_stream.get("r_frame_rate")),
        "avg_frame_rate": video_stream.get("avg_frame_rate"),
        "avg_frame_rate_fps": fraction_to_float(video_stream.get("avg_frame_rate")),
        "time_base": video_stream.get("time_base"),
        "decoded_frame_count": len(frames),
        "pts_frame_count": len(numeric_times),
        "pts_start_seconds": numeric_times[0] if numeric_times else None,
        "pts_end_seconds": numeric_times[-1] if numeric_times else None,
        "frame_interval_ms_median": median_delta * 1000.0 if median_delta else None,
        "frame_interval_ms_min": min_delta * 1000.0 if min_delta else None,
        "frame_interval_ms_max": max_delta * 1000.0 if max_delta else None,
        "variable_frame_rate_suspected": vfr_suspected,
        "vfr_detection_rule": "max_delta-min_delta > max(1ms, 5% of median_delta)",
        "duplicate_pts_count": duplicate_pts,
        "non_monotonic_pts_count": non_monotonic_pts,
        "audio_stream_count": len(audio_streams),
        "audio_streams": [
            {
                key: stream.get(key)
                for key in (
                    "index",
                    "codec_name",
                    "sample_rate",
                    "channels",
                    "channel_layout",
                    "duration",
                )
            }
            for stream in audio_streams
        ],
        "playback_speed": "unknown",
        "warnings": warnings,
        "truth_boundary": (
            "Decoded frame/audio evidence does not prove player, compositor, display, "
            "input, haptic, or human-perception identity."
        ),
    }


def capture_context(source: Path, source_sha256: str) -> Dict[str, Any]:
    return {
        "schema_version": "2.0",
        "status": "INCOMPLETE",
        "source": {
            "path": str(source),
            "sha256": source_sha256,
            "evidence_route": "VIDEO_ONLY",
            "rights_and_privacy": "unknown",
        },
        "presentation": {
            "player_or_runtime": "unknown",
            "player_version": "unknown",
            "playback_speed": "unknown",
            "playback_speed_evidence": "none",
            "viewport_px": "unknown",
            "device_pixel_ratio": "unknown",
            "display_resolution_px": "unknown",
            "display_refresh_hz": "unknown",
            "display_color_profile": "unknown",
            "hdr_tone_mapping": "unknown",
            "os_and_version": "unknown",
            "browser_and_version": "unknown",
            "reduced_motion": "unknown",
        },
        "input": {
            "modality": "unknown",
            "device": "unknown",
            "event_telemetry_available": False,
        },
        "audio": {
            "enabled": "unknown",
            "output_chain": "unknown",
            "latency_calibrated": False,
        },
        "haptics": {
            "present_in_target": "unknown",
            "telemetry_available": False,
            "target_device_test_available": False,
        },
        "runtime_evidence": {
            "source_available": False,
            "live_url_available": False,
            "dom_or_native_tree": False,
            "computed_styles": False,
            "animation_objects": False,
            "state_events": False,
            "network_and_console": False,
        },
        "open_decisions": [],
    }


def write_timeline(
    frames: Sequence[Dict[str, Any]],
    path: Path,
    artifacts: Optional[Dict[int, Path]] = None,
    root: Optional[Path] = None,
) -> None:
    fieldnames = [
        "frame_index",
        "pts",
        "pts_time",
        "best_effort_timestamp",
        "best_effort_timestamp_time",
        "pkt_duration",
        "pkt_duration_time",
        "key_frame",
        "pict_type",
        "repeat_pict",
        "width",
        "height",
        "pix_fmt",
        "color_range",
        "color_space",
        "color_primaries",
        "color_transfer",
        "artifact_path",
        "artifact_sha256",
    ]
    artifacts = artifacts or {}
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, frame in enumerate(frames):
            artifact = artifacts.get(index)
            artifact_path = ""
            artifact_hash = ""
            if artifact and artifact.is_file():
                artifact_path = str(artifact.relative_to(root)) if root else str(artifact)
                artifact_hash = sha256_file(artifact)
            writer.writerow(
                {
                    "frame_index": index,
                    "pts": frame.get("pts", ""),
                    "pts_time": frame.get("pts_time", ""),
                    "best_effort_timestamp": frame.get("best_effort_timestamp", ""),
                    "best_effort_timestamp_time": frame.get(
                        "best_effort_timestamp_time", ""
                    ),
                    "pkt_duration": frame.get("pkt_duration", ""),
                    "pkt_duration_time": frame.get("pkt_duration_time", ""),
                    "key_frame": frame.get("key_frame", ""),
                    "pict_type": frame.get("pict_type", ""),
                    "repeat_pict": frame.get("repeat_pict", ""),
                    "width": frame.get("width", ""),
                    "height": frame.get("height", ""),
                    "pix_fmt": frame.get("pix_fmt", ""),
                    "color_range": frame.get("color_range", ""),
                    "color_space": frame.get("color_space", ""),
                    "color_primaries": frame.get("color_primaries", ""),
                    "color_transfer": frame.get("color_transfer", ""),
                    "artifact_path": artifact_path,
                    "artifact_sha256": artifact_hash,
                }
            )


def create_probe_artifacts(
    video: Path, out: Path, tools: Dict[str, str]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
    source_hash = sha256_file(video)
    raw = probe_streams(video, tools)
    frames = probe_frames(video, tools)
    if not frames:
        raise EvidenceError("ffprobe returned no decoded video frames")
    summary = build_probe_summary(raw, frames, source_hash)
    json_write(out / "probe_raw.json", raw)
    json_write(out / "frame_probe_raw.json", {"frames": frames})
    json_write(out / "probe_summary.json", summary)
    (out / "source.sha256").write_text(
        "{}  {}\n".format(source_hash, video.name), encoding="utf-8"
    )
    context_path = out / "capture_context.json"
    if not context_path.exists():
        json_write(context_path, capture_context(video, source_hash))
    write_timeline(frames, out / "frame_timeline.csv")
    return raw, frames, summary


def select_uniform_indices(frames: Sequence[Dict[str, Any]], count: int) -> List[int]:
    if count <= 0 or not frames:
        return []
    count = min(count, len(frames))
    normalized = normalize_frames(frames)
    timed = [(item["_index"], item["_time"]) for item in normalized if item["_time"] is not None]
    if len(timed) >= 2:
        start = float(timed[0][1])
        end = float(timed[-1][1])
        if count == 1 or end <= start:
            return [timed[0][0]]
        targets = [start + (end - start) * step / float(count - 1) for step in range(count)]
        chosen = []
        for target in targets:
            index, _ = min(timed, key=lambda pair: abs(float(pair[1]) - target))
            if index not in chosen:
                chosen.append(index)
        return chosen
    if count == 1:
        return [0]
    return sorted(
        {
            int(round((len(frames) - 1) * step / float(count - 1)))
            for step in range(count)
        }
    )


def nearest_frame_index(frames: Sequence[Dict[str, Any]], timestamp: float) -> int:
    timed = [
        (index, frame_time(frame))
        for index, frame in enumerate(frames)
        if frame_time(frame) is not None
    ]
    if timed:
        return min(timed, key=lambda pair: abs(float(pair[1]) - timestamp))[0]
    return max(0, min(len(frames) - 1, int(round(timestamp))))


def crop_filter(crop: Optional[str]) -> List[str]:
    if not crop:
        return []
    if not re.match(r"^\d+:\d+:\d+:\d+$", crop):
        raise EvidenceError("crop must be w:h:x:y with non-negative integers")
    return ["crop={}".format(crop)]


def extract_one_frame(
    video: Path,
    out_file: Path,
    frame_index: int,
    tools: Dict[str, str],
    crop: Optional[str] = None,
) -> None:
    filters = crop_filter(crop)
    filters.append("select=eq(n\\,{})".format(frame_index))
    out_file.parent.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            tools["ffmpeg"],
            "-v",
            "error",
            "-y",
            "-i",
            str(video),
            "-map",
            "0:v:0",
            "-vf",
            ",".join(filters),
            "-frames:v",
            "1",
            "-fps_mode",
            "passthrough",
            str(out_file),
        ]
    )
    if not out_file.is_file():
        raise EvidenceError("frame extraction produced no file: {}".format(out_file))


def extract_overview(
    video: Path,
    out: Path,
    frames: Sequence[Dict[str, Any]],
    count: int,
    tools: Dict[str, str],
    crop: Optional[str],
) -> Tuple[Dict[int, Path], List[Dict[str, Any]]]:
    directory = out / "frames" / "overview"
    directory.mkdir(parents=True, exist_ok=True)
    mapping: Dict[int, Path] = {}
    index_rows = []
    for sequence, frame_index in enumerate(select_uniform_indices(frames, count), start=1):
        path = directory / "overview_{:03d}.png".format(sequence)
        extract_one_frame(video, path, frame_index, tools, crop=crop)
        mapping[frame_index] = path
        index_rows.append(
            {
                "sequence": sequence,
                "frame_index": frame_index,
                "pts_time": frame_time(frames[frame_index]),
                "artifact_path": str(path.relative_to(out)),
                "sha256": sha256_file(path),
            }
        )
    json_write(directory / "overview_index.json", index_rows)
    return mapping, index_rows


def make_contact_sheet(
    overview_directory: Path, count: int, out_file: Path, tools: Dict[str, str]
) -> Optional[Path]:
    if count <= 0:
        return None
    columns = min(4, count)
    rows = int(math.ceil(count / float(columns)))
    pattern = overview_directory / "overview_%03d.png"
    result = run_command(
        [
            tools["ffmpeg"],
            "-v",
            "error",
            "-y",
            "-framerate",
            "1",
            "-start_number",
            "1",
            "-i",
            str(pattern),
            "-vf",
            "scale=-2:240,tile={}x{}:padding=6:margin=6:color=gray".format(
                columns, rows
            ),
            "-frames:v",
            "1",
            str(out_file),
        ],
        check=False,
    )
    return out_file if result.returncode == 0 and out_file.is_file() else None


def extract_exhaustive(
    video: Path, out: Path, frames: Sequence[Dict[str, Any]], tools: Dict[str, str]
) -> Dict[int, Path]:
    directory = out / "frames" / "all"
    directory.mkdir(parents=True, exist_ok=True)
    pattern = directory / "frame_%08d.png"
    run_command(
        [
            tools["ffmpeg"],
            "-v",
            "error",
            "-y",
            "-i",
            str(video),
            "-map",
            "0:v:0",
            "-fps_mode",
            "passthrough",
            "-start_number",
            "0",
            str(pattern),
        ]
    )
    files = sorted(directory.glob("frame_*.png"))
    if not files:
        raise EvidenceError(
            "focused window produced no decoded frames: {:.6f}:{:.6f}".format(start, end)
        )
    if len(files) != len(frames):
        raise EvidenceError(
            "decoded/extracted count mismatch: ffprobe={} ffmpeg={}".format(
                len(frames), len(files)
            )
        )
    return {index: path for index, path in enumerate(files)}


def parse_showinfo(text: str) -> List[Dict[str, Any]]:
    rows = []
    for line in text.splitlines():
        match = SHOWINFO_RE.search(line)
        if not match:
            continue
        rows.append(
            {
                "output_index": int(match.group("n")),
                "pts": int(match.group("pts")),
                "pts_time": float(match.group("pts_time")),
            }
        )
    return rows


def extract_scene_frames(
    video: Path,
    out: Path,
    frames: Sequence[Dict[str, Any]],
    threshold: float,
    max_scenes: int,
    tools: Dict[str, str],
    crop: Optional[str],
) -> List[Dict[str, Any]]:
    directory = out / "frames" / "scenes"
    directory.mkdir(parents=True, exist_ok=True)
    filters = crop_filter(crop)
    filters.extend(["select=gt(scene\\,{:.6f})".format(threshold), "showinfo"])
    result = run_command(
        [
            tools["ffmpeg"],
            "-v",
            "info",
            "-y",
            "-i",
            str(video),
            "-map",
            "0:v:0",
            "-vf",
            ",".join(filters),
            "-frames:v",
            str(max_scenes),
            "-fps_mode",
            "passthrough",
            str(directory / "scene_%05d.png"),
        ]
    )
    (directory / "scene_showinfo.log").write_text(result.stderr, encoding="utf-8")
    rows = parse_showinfo(result.stderr)
    files = sorted(directory.glob("scene_*.png"))
    index_rows = []
    for sequence, path in enumerate(files):
        info = rows[sequence] if sequence < len(rows) else {}
        timestamp = info.get("pts_time")
        source_index = nearest_frame_index(frames, timestamp) if timestamp is not None else None
        index_rows.append(
            {
                "sequence": sequence + 1,
                "source_frame_index": source_index,
                "pts_time": timestamp,
                "artifact_path": str(path.relative_to(out)),
                "sha256": sha256_file(path),
                "threshold": threshold,
            }
        )
    json_write(directory / "scene_index.json", index_rows)
    return index_rows


def extract_window_frames(
    video: Path,
    out: Path,
    frames: Sequence[Dict[str, Any]],
    start: float,
    end: float,
    label: str,
    tools: Dict[str, str],
    crop: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if end <= start:
        raise EvidenceError("window end must be greater than start")
    safe_label = re.sub(r"[^a-zA-Z0-9._-]+", "_", label).strip("._") or "window"
    directory = out / "windows" / safe_label
    directory.mkdir(parents=True, exist_ok=True)
    filters = crop_filter(crop)
    filters.extend(
        [
            "select=between(t\\,{:.9f}\\,{:.9f})".format(start, end),
            "showinfo",
        ]
    )
    result = run_command(
        [
            tools["ffmpeg"],
            "-v",
            "info",
            "-y",
            "-i",
            str(video),
            "-map",
            "0:v:0",
            "-vf",
            ",".join(filters),
            "-fps_mode",
            "passthrough",
            "-start_number",
            "0",
            str(directory / "frame_%08d.png"),
        ]
    )
    (directory / "showinfo.log").write_text(result.stderr, encoding="utf-8")
    rows = parse_showinfo(result.stderr)
    files = sorted(directory.glob("frame_*.png"))
    index_rows = []
    for sequence, path in enumerate(files):
        info = rows[sequence] if sequence < len(rows) else {}
        timestamp = info.get("pts_time")
        source_index = nearest_frame_index(frames, timestamp) if timestamp is not None else None
        index_rows.append(
            {
                "sequence": sequence,
                "source_frame_index": source_index,
                "pts_time": timestamp,
                "artifact_path": str(path.relative_to(out)),
                "sha256": sha256_file(path),
                "window_start": start,
                "window_end": end,
            }
        )
    json_write(directory / "window_index.json", index_rows)
    return index_rows


def parse_motion_metadata(text: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    for line in text.splitlines():
        frame_match = METADATA_FRAME_RE.search(line)
        if frame_match:
            if current is not None:
                rows.append(current)
            current = {
                "frame": int(frame_match.group("n")),
                "pts": int(frame_match.group("pts")),
                "pts_time": float(frame_match.group("pts_time")),
                "yavg_difference": None,
            }
            continue
        yavg_match = YAVG_RE.search(line)
        if yavg_match and current is not None:
            current["yavg_difference"] = float(yavg_match.group("value"))
    if current is not None:
        rows.append(current)
    return rows


def extract_motion_signal(
    video: Path, out: Path, tools: Dict[str, str], crop: Optional[str]
) -> List[Dict[str, Any]]:
    directory = out / "motion"
    directory.mkdir(parents=True, exist_ok=True)
    filters = crop_filter(crop)
    filters.extend(
        [
            "tblend=all_mode=difference",
            "signalstats",
            "metadata=mode=print",
        ]
    )
    result = run_command(
        [
            tools["ffmpeg"],
            "-v",
            "info",
            "-i",
            str(video),
            "-map",
            "0:v:0",
            "-vf",
            ",".join(filters),
            "-an",
            "-f",
            "null",
            "-",
        ]
    )
    raw_path = directory / "motion_metadata.log"
    raw_path.write_text(result.stderr, encoding="utf-8")
    rows = parse_motion_metadata(result.stderr)
    with (directory / "motion_signal.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["frame", "pts", "pts_time", "yavg_difference"]
        )
        writer.writeheader()
        writer.writerows(rows)
    return rows


def extract_audio(
    video: Path, out: Path, summary: Dict[str, Any], tools: Dict[str, str]
) -> Optional[Path]:
    if not summary.get("audio_stream_count"):
        return None
    directory = out / "audio"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "reference_pcm_s24le.wav"
    run_command(
        [
            tools["ffmpeg"],
            "-v",
            "error",
            "-y",
            "-i",
            str(video),
            "-map",
            "0:a:0",
            "-vn",
            "-c:a",
            "pcm_s24le",
            str(path),
        ]
    )
    return path if path.is_file() else None


def duplicate_groups(artifacts: Dict[int, Path]) -> Dict[str, List[int]]:
    groups: Dict[str, List[int]] = {}
    for frame_index, path in artifacts.items():
        groups.setdefault(sha256_file(path), []).append(frame_index)
    return {digest: indexes for digest, indexes in groups.items() if len(indexes) > 1}


def write_review_files(
    out: Path,
    frames: Sequence[Dict[str, Any]],
    artifacts: Dict[int, Path],
    batch_size: int,
) -> None:
    if batch_size <= 0:
        raise EvidenceError("review batch size must be positive")
    digest_to_indexes: Dict[str, List[int]] = {}
    rows = []
    for frame_index in sorted(artifacts):
        path = artifacts[frame_index]
        digest = sha256_file(path)
        digest_to_indexes.setdefault(digest, []).append(frame_index)
    representatives = {
        digest: indexes[0] for digest, indexes in digest_to_indexes.items()
    }
    for frame_index in sorted(artifacts):
        path = artifacts[frame_index]
        digest = sha256_file(path)
        representative = representatives[digest]
        rows.append(
            {
                "frame_index": frame_index,
                "pts_time": frame_time(frames[frame_index]),
                "artifact_path": str(path.relative_to(out)),
                "sha256": digest,
                "duplicate_of": "" if representative == frame_index else representative,
                "status": "",
                "notes": "",
            }
        )

    with (out / "FRAME_REVIEW_LEDGER.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        fieldnames = [
            "frame_index",
            "pts_time",
            "artifact_path",
            "sha256",
            "duplicate_of",
            "status",
            "notes",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    review_indexes = [
        row["frame_index"] for row in rows if row["duplicate_of"] == ""
    ]
    batches = []
    for offset in range(0, len(review_indexes), batch_size):
        indexes = review_indexes[offset : offset + batch_size]
        batches.append(
            {
                "batch_id": len(batches) + 1,
                "frame_indexes": indexes,
                "artifact_paths": [str(artifacts[index].relative_to(out)) for index in indexes],
            }
        )
    json_write(
        out / "review_batches.json",
        {
            "batch_size": batch_size,
            "unique_exact_frames_to_review": len(review_indexes),
            "exact_duplicate_frame_count": len(rows) - len(review_indexes),
            "batches": batches,
            "duplicate_groups": [
                {"sha256": digest, "frame_indexes": indexes}
                for digest, indexes in sorted(digest_to_indexes.items())
                if len(indexes) > 1
            ],
        },
    )


def evidence_files(out: Path) -> Iterable[Path]:
    for path in sorted(out.rglob("*")):
        if not path.is_file():
            continue
        if path.name in MUTABLE_EVIDENCE_FILES:
            continue
        yield path


def write_hash_manifest(out: Path) -> int:
    lines = []
    for path in evidence_files(out):
        relative = path.relative_to(out)
        lines.append("{}  {}".format(sha256_file(path), relative.as_posix()))
    (out / "EVIDENCE_MANIFEST.sha256").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return len(lines)


def verify_hash_manifest(out: Path) -> List[str]:
    path = out / "EVIDENCE_MANIFEST.sha256"
    errors = []
    if not path.is_file():
        return ["missing EVIDENCE_MANIFEST.sha256"]
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            expected, relative = line.split("  ", 1)
        except ValueError:
            errors.append("invalid manifest line {}".format(line_number))
            continue
        target = out / relative
        try:
            target.resolve().relative_to(out.resolve())
        except ValueError:
            errors.append("manifest path escapes evidence root: {}".format(relative))
            continue
        if not target.is_file():
            errors.append("missing evidence file: {}".format(relative))
            continue
        actual = sha256_file(target)
        if actual != expected:
            errors.append("hash mismatch: {}".format(relative))
    return errors


def validate_review_ledger(out: Path) -> List[str]:
    path = out / "FRAME_REVIEW_LEDGER.csv"
    if not path.is_file():
        return ["missing FRAME_REVIEW_LEDGER.csv"]
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    by_index = {str(row.get("frame_index")): row for row in rows}
    errors = []
    for row in rows:
        index = str(row.get("frame_index"))
        status = (row.get("status") or "").strip()
        duplicate_of = (row.get("duplicate_of") or "").strip()
        if status not in PASS_REVIEW_STATUSES:
            errors.append("frame {} not reviewed: status={!r}".format(index, status))
            continue
        if status == "duplicate_verified":
            if not duplicate_of:
                errors.append("frame {} marked duplicate without duplicate_of".format(index))
                continue
            representative = by_index.get(duplicate_of)
            if not representative or representative.get("status") != "reviewed":
                errors.append(
                    "frame {} duplicate representative {} is not reviewed".format(
                        index, duplicate_of
                    )
                )
        artifact = out / str(row.get("artifact_path") or "")
        if not artifact.is_file():
            errors.append("frame {} artifact missing".format(index))
        elif sha256_file(artifact) != row.get("sha256"):
            errors.append("frame {} artifact hash changed".format(index))
    return errors


def doctor_payload() -> Dict[str, Any]:
    tools = {name: tool_path(name) for name in REQUIRED_TOOLS}
    missing = [name for name, path in tools.items() if not path]
    filters: Dict[str, bool] = {}
    fps_mode_supported = False
    if tools.get("ffmpeg"):
        filter_result = run_command([str(tools["ffmpeg"]), "-filters"], check=False)
        filter_text = (filter_result.stdout or "") + (filter_result.stderr or "")
        for name in ("select", "showinfo", "tblend", "signalstats", "metadata", "ssim", "psnr", "libvmaf"):
            filters[name] = bool(re.search(r"\b{}\b".format(re.escape(name)), filter_text))
        help_result = run_command([str(tools["ffmpeg"]), "-h", "full"], check=False)
        help_text = (help_result.stdout or "") + (help_result.stderr or "")
        fps_mode_supported = "fps_mode" in help_text
    required_filters = ("select", "showinfo", "tblend", "signalstats", "metadata")
    missing_filters = [name for name in required_filters if not filters.get(name)]
    return {
        "schema_version": "2.0",
        "script_version": VERSION,
        "python": sys.version.split()[0],
        "tools": {
            name: {"path": path, "version": tool_version(name) if path else None}
            for name, path in tools.items()
        },
        "missing_required_binaries": missing,
        "ffmpeg_fps_mode_supported": fps_mode_supported,
        "ffmpeg_filters": filters,
        "missing_required_filters": missing_filters,
        "optional_metrics": {
            "ssim": filters.get("ssim", False),
            "psnr": filters.get("psnr", False),
            "libvmaf": filters.get("libvmaf", False),
        },
        "ready": not missing and not missing_filters and fps_mode_supported,
    }


def command_doctor(_args: argparse.Namespace) -> int:
    payload = doctor_payload()
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["ready"] else 2


def command_probe(args: argparse.Namespace) -> int:
    tools = require_tools()
    video = ensure_video(args.video)
    out = prepare_new_output(args.out)
    _raw, _frames, summary = create_probe_artifacts(video, out, tools)
    write_hash_manifest(out)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def parse_window(value: str) -> Tuple[float, float]:
    if value.count(":") == 1:
        start_text, end_text = value.split(":", 1)
        return parse_time(start_text), parse_time(end_text)
    match = re.match(r"^(?P<start>.+?)-(?P<end>.+)$", value)
    if match:
        return parse_time(match.group("start")), parse_time(match.group("end"))
    raise EvidenceError(
        "window must use simple seconds START:END (for example 1.20:2.10)"
    )


def command_extract(args: argparse.Namespace) -> int:
    if args.uniform <= 0:
        raise EvidenceError("--uniform must be positive")
    if not (0.0 <= args.scene_threshold <= 1.0):
        raise EvidenceError("--scene-threshold must be between 0 and 1")
    if args.max_scenes <= 0:
        raise EvidenceError("--max-scenes must be positive")
    if args.review_batch_size <= 0:
        raise EvidenceError("--review-batch-size must be positive")
    tools = require_tools()
    video = ensure_video(args.video)
    out = prepare_new_output(args.out)
    _raw, frames, summary = create_probe_artifacts(video, out, tools)

    overview_artifacts, overview_rows = extract_overview(
        video, out, frames, args.uniform, tools, crop=args.crop
    )
    contact = make_contact_sheet(
        out / "frames" / "overview",
        len(overview_rows),
        out / "frames" / "contact.png",
        tools,
    )

    scene_rows = extract_scene_frames(
        video,
        out,
        frames,
        args.scene_threshold,
        args.max_scenes,
        tools,
        crop=args.crop,
    )

    window_rows = []
    for number, value in enumerate(args.window or [], start=1):
        start, end = parse_window(value)
        rows = extract_window_frames(
            video,
            out,
            frames,
            start,
            end,
            "window_{:03d}_{:.3f}_{:.3f}".format(number, start, end),
            tools,
            crop=args.crop,
        )
        window_rows.append({"start": start, "end": end, "frames": len(rows)})

    motion_rows = extract_motion_signal(video, out, tools, crop=args.crop)
    audio_path = extract_audio(video, out, summary, tools)

    if args.mode == "exhaustive":
        coverage_artifacts = extract_exhaustive(video, out, frames, tools)
        coverage_scope = "all_decoded_frames"
    else:
        coverage_artifacts = overview_artifacts
        coverage_scope = "uniform_overview_only_plus_scene_and_explicit_windows"

    write_timeline(
        frames,
        out / "frame_timeline.csv",
        artifacts=coverage_artifacts if args.mode == "exhaustive" else None,
        root=out,
    )
    write_review_files(out, frames, coverage_artifacts, batch_size=args.review_batch_size)

    manifest = {
        "schema_version": "2.0",
        "script_version": VERSION,
        "mode": args.mode,
        "coverage_scope": coverage_scope,
        "source_sha256": summary["source_sha256"],
        "decoded_frame_count": len(frames),
        "coverage_artifact_count": len(coverage_artifacts),
        "overview_frame_count": len(overview_rows),
        "scene_frame_count": len(scene_rows),
        "windows": window_rows,
        "motion_signal_rows": len(motion_rows),
        "audio_extracted": bool(audio_path),
        "contact_sheet": str(contact.relative_to(out)) if contact else None,
        "crop_applied_to_derivatives": args.crop,
        "native_exhaustive_frames_are_uncropped": args.mode == "exhaustive",
        "mutable_files_excluded_from_hash_manifest": sorted(MUTABLE_EVIDENCE_FILES),
        "status": "BLOCKED_REVIEW",
    }
    manifest["immutable_hashed_file_count"] = len(list(evidence_files(out))) + 1
    json_write(out / "extraction_manifest.json", manifest)
    write_hash_manifest(out)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_frame(args: argparse.Namespace) -> int:
    tools = require_tools()
    video = ensure_video(args.video)
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    frames = probe_frames(video, tools)
    if not frames:
        raise EvidenceError("ffprobe returned no decoded video frames")
    timestamp = parse_time(args.timestamp)
    index = nearest_frame_index(frames, timestamp)
    path = out / "key_frame_{:08d}_t{:010d}ms.png".format(index, int(round(timestamp * 1000)))
    extract_one_frame(video, path, index, tools, crop=args.crop)
    payload = {
        "requested_time": timestamp,
        "source_frame_index": index,
        "source_pts_time": frame_time(frames[index]),
        "artifact_path": str(path),
        "sha256": sha256_file(path),
    }
    json_write(path.with_suffix(".json"), payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_window(args: argparse.Namespace) -> int:
    tools = require_tools()
    video = ensure_video(args.video)
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    frames = probe_frames(video, tools)
    if not frames:
        raise EvidenceError("ffprobe returned no decoded video frames")
    start = parse_time(args.start)
    end = parse_time(args.end)
    rows = extract_window_frames(
        video,
        out,
        frames,
        start,
        end,
        args.label,
        tools,
        crop=args.crop,
    )
    payload = {"start": start, "end": end, "frame_count": len(rows), "label": args.label}
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_validate(args: argparse.Namespace) -> int:
    out = Path(args.evidence).expanduser().resolve()
    errors = []
    warnings = []
    if not out.is_dir():
        errors.append("evidence directory does not exist")
    manifest_path = out / "extraction_manifest.json"
    manifest: Dict[str, Any] = {}
    if not manifest_path.is_file():
        errors.append("missing extraction_manifest.json")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for required in ("probe_summary.json", "frame_timeline.csv", "review_batches.json"):
        if not (out / required).is_file():
            errors.append("missing {}".format(required))
    errors.extend(verify_hash_manifest(out))

    if manifest.get("mode") == "exhaustive":
        files = sorted((out / "frames" / "all").glob("frame_*.png"))
        expected = int(manifest.get("decoded_frame_count") or 0)
        if len(files) != expected:
            errors.append(
                "exhaustive count mismatch: expected={} actual={}".format(expected, len(files))
            )
    elif args.require_reviewed:
        errors.append("--require-reviewed is only a full-coverage gate for exhaustive mode")

    if args.require_reviewed:
        errors.extend(validate_review_ledger(out))
    else:
        warnings.append("human frame-review coverage was not required in this validation")

    payload = {
        "schema_version": "2.0",
        "passed": not errors,
        "mode": manifest.get("mode"),
        "errors": errors,
        "warnings": warnings,
    }
    json_write(out / "validation_result.json", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and validate evidence for video-replica", prog="video_evidence.py"
    )
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="check required binaries and filters")
    doctor.set_defaults(func=command_doctor)

    probe = subparsers.add_parser("probe", help="write stream/frame timeline evidence")
    probe.add_argument("video")
    probe.add_argument("out")
    probe.set_defaults(func=command_probe)

    extract = subparsers.add_parser("extract", help="extract an evidence pack")
    extract.add_argument("video")
    extract.add_argument("out")
    extract.add_argument("--mode", choices=("balanced", "exhaustive"), default="balanced")
    extract.add_argument("--uniform", type=int, default=16)
    extract.add_argument("--scene-threshold", type=float, default=0.12)
    extract.add_argument("--max-scenes", type=int, default=32)
    extract.add_argument("--window", action="append", default=[])
    extract.add_argument("--crop", help="review derivative crop w:h:x:y; exhaustive frames remain native")
    extract.add_argument("--review-batch-size", type=int, default=16)
    extract.set_defaults(func=command_extract)

    frame = subparsers.add_parser("frame", help="extract the decoded frame nearest a time")
    frame.add_argument("video")
    frame.add_argument("out")
    frame.add_argument("timestamp")
    frame.add_argument("--crop")
    frame.set_defaults(func=command_frame)

    window = subparsers.add_parser("window", help="extract every native-rate frame in a time window")
    window.add_argument("video")
    window.add_argument("out")
    window.add_argument("start")
    window.add_argument("end")
    window.add_argument("--label", default="focused_window")
    window.add_argument("--crop")
    window.set_defaults(func=command_window)

    validate = subparsers.add_parser("validate", help="verify hashes/counts and optional human review")
    validate.add_argument("evidence")
    validate.add_argument("--require-reviewed", action="store_true")
    validate.set_defaults(func=command_validate)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except EvidenceError as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("ERROR: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
