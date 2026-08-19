#!/usr/bin/env python3
"""Run the pilot tasks through the local ComfyUI, for an A/B against MiniMax.

The point of running locally is not the checkpoint — Midjourney Niji 7 is a
strong anime model on its own. It is that two of the hardest clauses in
`ACCEPTANCE.md` stop being requests and become mechanics:

*   **C1/C2, character inside the left 35%.** IPAdapter takes an `attn_mask`,
    so the character reference only has attention where the mask is white. The
    subject is confined by construction rather than by asking politely.
*   **G2/G3, the day and night versions sharing one scene.** Same seed, same
    latent, same graph, one differing prompt clause — the pair is deterministic
    instead of two independent rolls of the dice.

Everything else (identity from the anchor, banned scenery, no text) is carried
by the same prompts the MiniMax pack uses, so the comparison isolates the
engine rather than the brief.

Usage:
    python3 comfy_run.py --pilot /tmp/pilot --out /tmp/comfy-out
    python3 comfy_run.py --pilot /tmp/pilot --out /tmp/comfy-out --only ganyu
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
import uuid
from pathlib import Path

from PIL import Image

HOST = "http://127.0.0.1:8188"
CHECKPOINT = "Illustrious-XL-v2.0.safetensors"
IPADAPTER = "ip-adapter-plus_sdxl_vit-h.safetensors"
CLIP_VISION = "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"

# SDXL is trained near 1M pixels; 1344x768 is the standard 16:9 bucket. The
# deliverable is 2560x1440, reached by a latent upscale pass rather than
# generating oversize (which produces duplicated limbs on SDXL).
BASE_W, BASE_H = 1344, 768
FINAL_W, FINAL_H = 2560, 1440
SUBJECT_FRACTION = 0.35

# Illustrious responds to danbooru-style tags; the pack's prose prompt is kept
# and prefixed with quality tags rather than rewritten, so both engines answer
# the same brief.
QUALITY = "masterpiece, best quality, absurdres, very aesthetic, official art, "


def post(path: str, payload: dict) -> dict:
    request = urllib.request.Request(
        f"{HOST}{path}", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def get(path: str) -> dict:
    with urllib.request.urlopen(f"{HOST}{path}", timeout=60) as response:
        return json.load(response)


def upload(path: Path, name: str) -> str:
    """Upload one image into ComfyUI's input dir; returns the stored name."""
    boundary = uuid.uuid4().hex
    body = b"".join([
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; "
        f"filename=\"{name}\"\r\nContent-Type: image/png\r\n\r\n".encode(),
        path.read_bytes(), b"\r\n",
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n".encode(),
        f"--{boundary}--\r\n".encode(),
    ])
    request = urllib.request.Request(
        f"{HOST}/upload/image", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)["name"]


def make_mask(target: Path) -> None:
    """White over the left `SUBJECT_FRACTION`, black elsewhere.

    IPAdapter reads white as "apply the reference here", so this is what keeps
    the character — hair, skirt and all — out of the right two thirds where the
    chat column sits.
    """
    mask = Image.new("RGB", (BASE_W, BASE_H), "black")
    edge = int(BASE_W * SUBJECT_FRACTION)
    mask.paste(Image.new("RGB", (edge, BASE_H), "white"), (0, 0))
    target.parent.mkdir(parents=True, exist_ok=True)
    mask.save(target)


def graph(anchor: str, mask: str, positive: str, negative: str, seed: int) -> dict:
    """The workflow, in ComfyUI's API format."""
    return {
        "1": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": CHECKPOINT}},
        "2": {"class_type": "CLIPTextEncode",
              "inputs": {"text": QUALITY + positive, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode",
              "inputs": {"text": negative, "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage",
              "inputs": {"width": BASE_W, "height": BASE_H, "batch_size": 1}},
        "5": {"class_type": "LoadImage", "inputs": {"image": anchor}},
        "6": {"class_type": "LoadImage", "inputs": {"image": mask}},
        "7": {"class_type": "ImageToMask", "inputs": {"image": ["6", 0], "channel": "red"}},
        "8": {"class_type": "IPAdapterModelLoader", "inputs": {"ipadapter_file": IPADAPTER}},
        "9": {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": CLIP_VISION}},
        "10": {"class_type": "IPAdapterAdvanced",
               "inputs": {"model": ["1", 0], "ipadapter": ["8", 0], "image": ["5", 0],
                          "clip_vision": ["9", 0], "attn_mask": ["7", 0],
                          "weight": 0.85, "weight_type": "linear", "combine_embeds": "concat",
                          "start_at": 0.0, "end_at": 1.0, "embeds_scaling": "V only"}},
        "11": {"class_type": "KSampler",
               "inputs": {"model": ["10", 0], "positive": ["2", 0], "negative": ["3", 0],
                          "latent_image": ["4", 0], "seed": seed, "steps": 30, "cfg": 5.5,
                          "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0}},
        "12": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["1", 2]}},
        "13": {"class_type": "ImageScale",
               "inputs": {"image": ["12", 0], "width": FINAL_W, "height": FINAL_H,
                          "upscale_method": "lanczos", "crop": "disabled"}},
        "14": {"class_type": "SaveImage",
               "inputs": {"images": ["13", 0], "filename_prefix": "harnessui"}},
    }


def run(workflow: dict, *, budget: int = 900) -> list[str]:
    """Queue one graph and wait; returns the produced filenames."""
    client = uuid.uuid4().hex
    prompt_id = post("/prompt", {"prompt": workflow, "client_id": client})["prompt_id"]
    deadline = time.time() + budget
    while time.time() < deadline:
        history = get(f"/history/{prompt_id}")
        if prompt_id in history:
            entry = history[prompt_id]
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                messages = [m for m in status.get("messages", []) if m[0] == "execution_error"]
                raise RuntimeError(str(messages)[:300] if messages else "execution error")
            files = []
            for output in entry.get("outputs", {}).values():
                files += [image["filename"] for image in output.get("images", [])]
            if files:
                return files
        time.sleep(3)
    raise TimeoutError(f"{budget}s 内未完成")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", action="append")
    parser.add_argument("--seed", type=int, default=20260819)
    args = parser.parse_args()

    manifest = json.loads((args.pilot / "manifest.json").read_text(encoding="utf-8"))
    tasks = manifest["tasks"]
    if args.only:
        tasks = [t for t in tasks if any(k in t["id"] for k in args.only)]

    staging = args.out / "_staging"
    mask_path = staging / "harnessui_left35_mask.png"
    make_mask(mask_path)
    mask_name = upload(mask_path, mask_path.name)
    print(f"构图遮罩已上传：{mask_name}  (左 {SUBJECT_FRACTION:.0%} 白)")

    comfy_output = Path("/Volumes/share/03_资料库/ComfyUI-Output")
    args.out.mkdir(parents=True, exist_ok=True)
    done = failed = 0

    for task in tasks:
        anchor_src = args.pilot / task["anchor"]
        anchor_name = upload(anchor_src, f"anchor_{task['character']}_{task['variant']}.png")
        for side in ("light", "dark"):
            label = f"{task['character']}-{task['variant']}-{side}"
            try:
                files = run(graph(anchor_name, mask_name,
                                  task["outputs"][side]["prompt"],
                                  task["negative_prompt"], args.seed))
            except Exception as error:
                failed += 1
                print(f"  ✗ {label:<40} {str(error)[:90]}")
                continue
            for name in files:
                source = comfy_output / name
                if not source.exists():
                    matches = list(comfy_output.rglob(name))
                    source = matches[0] if matches else None
                if source is None:
                    print(f"  ? {label:<40} 产物找不到 {name}")
                    continue
                target = args.out / f"{label}.png"
                target.write_bytes(source.read_bytes())
                done += 1
                print(f"  + {label:<40} {target.stat().st_size // 1024}KB")

    print(f"\n完成 {done} · 失败 {failed}")


if __name__ == "__main__":
    main()
