#!/usr/bin/env python3
"""定点重出：拿人工挑出来的缺陷清单，逐张重做。

跟 batch_run 的区别是这里走实时接口而不是批处理——重做的量是几张到几十张，
等一轮 batch（最长 24 小时）不值得，而且重做通常是用户盯着结果在等。

每张都带上"上一版错在哪"，否则重出就只是再掷一次骰子。缺陷描述由调用方给，
因为判定是人做的：自动判官试过三轮，复现不了用户的阈值。

原图不删，改名成 <side>.rejected-<n>.png 留在原地——万一新的更差，还能换回去。

Usage:
    python3 regen.py --ids zzz/lucia/whispering-dreams --sides light,dark \\
        --note "上一版握杖的手臂没有肩部连接，等于凭空多出一条手臂"
    python3 regen.py --from-list bad.txt          # 复核页导出的 "<id>|<side>" 清单
"""

from __future__ import annotations

import argparse
import base64
import json
import pathlib
import sys
import time
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import erotic_levels  # noqa: E402

ROOT = pathlib.Path.home() / ".harness-ui"
SIZE = "3840x2160"
MODEL = "gpt-image-2"

FIX = ("\n\nCRITICAL ANATOMY REQUIREMENTS — the previous attempt failed on these:\n"
       "Exactly two arms, each one clearly traceable from hand to wrist to forearm to "
       "upper arm to a visible shoulder joint on the correct side of the torso. No limb "
       "may emerge from the waist, ribs, armpit or back. Exactly two hands, five fingers "
       "each, with a visible thumb. Exactly two legs. Every prop, weapon, ribbon and "
       "accessory must have a visible attachment point — nothing floating unattached. "
       "No duplicated or fused body parts. "
       # 2026-08-21 新增：普罗米娅那两张是「头朝正面、躯干却背对镜头」，
       # 四肢数目全对，所以上面每一条都通过了，缺陷仍然一眼可见。
       "HEAD AND TORSO MUST FACE CONSISTENTLY: the direction the face looks and the "
       "direction the chest, shoulders and hips face must differ by no more than a "
       "natural head turn (about 45 degrees). Never render a frontal face on a torso "
       "that is turned away from the viewer, and never show the back of the body "
       "together with a front-facing head. The neck must connect the head to the "
       "shoulders on the anatomically correct side."
       "\n\nHANDS (the single most failure-prone part of this image): "
       "Exactly two hands total, no more. Each hand traces cleanly from fingertips to "
       "palm to wrist to forearm to upper arm to a visible shoulder joint on the correct "
       "side of the torso. Five fingers per hand with one clearly separate thumb; no sixth "
       "finger, no fused or duplicated fingers, no ghosted or doubled hand outline. "
       "Palm-versus-back orientation must follow the forearm's rotation the way a real hand "
       "does: the thumb sits on the radial side, and a visible palm means the forearm is "
       "supinated. Hands never intersect the chest, torso, hair or any prop — where a hand "
       "overlaps something, render a clear occlusion edge, not a blend. Both hands are "
       "rendered at the same focus and detail level as the face; a blurred or smudged hand "
       "is a defect even if everything else is sharp.")


def anchor_and_prompt(task_id: str, side: str, pack: pathlib.Path):
    manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
    task = next((t for t in manifest["tasks"] if t["id"] == task_id), None)
    if task is None:
        sys.exit(f"任务包里没有 {task_id}")
    return pack / task["anchor"], task["outputs"][side]["prompt"]


def generate(anchor: pathlib.Path, prompt: str, key: str) -> bytes:
    boundary = "----hu-regen"
    parts = []
    def field(name, value):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    field("model", MODEL)
    field("prompt", prompt)
    field("size", SIZE)
    field("n", "1")
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="image[]"; '
        f'filename="{anchor.name}"\r\nContent-Type: image/jpeg\r\n\r\n'.encode()
        + anchor.read_bytes() + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    request = urllib.request.Request(
        "https://api.openai.com/v1/images/edits", data=b"".join(parts),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(request, timeout=900) as response:
        payload = json.load(response)
    usage = payload.get("usage", {})
    cost = (usage.get("input_tokens_details", {}).get("image_tokens", 0) * 8
            + usage.get("input_tokens_details", {}).get("text_tokens", 0) * 5
            + usage.get("output_tokens", 0) * 30) / 1e6
    return base64.b64decode(payload["data"][0]["b64_json"]), cost


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=pathlib.Path,
                        default=pathlib.Path("/Users/linzezhang/Movies/Hub/Projects/根据任务包去执行和生成/taskpack"))
    parser.add_argument("--key-file", type=pathlib.Path, required=True)
    parser.add_argument("--ids", help="逗号分隔的 task id")
    parser.add_argument("--from-list", type=pathlib.Path, help="复核页导出的 <id>|<side> 清单")
    parser.add_argument("--sides", default="light,dark")
    parser.add_argument("--note", default="", help="这一版具体错在哪，写进 prompt")
    parser.add_argument("--level", type=int, choices=[1, 2, 3, 4, 5],
                        help="锁定色情度档位，不走 L4→L3→L2 阶梯（兜底时用 L1）")
    args = parser.parse_args()

    key = args.key_file.read_text().strip()
    jobs = []
    if args.from_list:
        for line in args.from_list.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "|" in line:
                task_id, side = line.split("|", 1)
                jobs.append((task_id, side))
    if args.ids:
        for task_id in args.ids.split(","):
            jobs += [(task_id.strip(), s) for s in args.sides.split(",")]
    if not jobs:
        sys.exit("没有要重做的")

    spent = 0.0
    for task_id, side in jobs:
        anchor, prompt = anchor_and_prompt(task_id, side, args.pack)
        target = ROOT / "master" / task_id / f"{side}.png"
        started = time.time()
        data = None
        # 色情度阶梯 L4 → L3 → L2。任务包里存的是 L5，直接用必被安全系统拦。
        ladder = [args.level] * 3 if args.level else [erotic_levels.level_for_attempt(a) for a in (1, 2, 3)]
        for level in ladder:
            full = (erotic_levels.at_level(prompt, level) + FIX
                    + (f" Specifically: {args.note}" if args.note else ""))
            try:
                data, cost = generate(anchor, full, key)
                spent += cost
                print(f"    {erotic_levels.NAMES[level]} 通过", flush=True)
                break
            except Exception as error:
                body = ""
                if hasattr(error, "read"):
                    try:
                        body = error.read().decode("utf-8", "replace")
                    except Exception:
                        body = ""
                blocked = "moderation_blocked" in body or "safety system" in body
                print(f"    {erotic_levels.NAMES[level]} "
                      f"{'被安全系统拦' if blocked else str(error)[:70]}", flush=True)
                if not blocked:
                    break
        if data is None:
            print(f"  ! {task_id} [{side}] 三档都没过，标记需重做")
            continue
        if target.exists():
            # 旧图留在原地改个名：新的不一定更好，得留退路
            n = 1
            while (spare := target.with_suffix(f".rejected-{n}.png")).exists():
                n += 1
            target.rename(spare)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f"  ✓ {task_id} [{side}] {time.time()-started:.0f}s  ${cost:.3f}  → {target}")

    print(f"\n重做 {len(jobs)} 张 · 花费 ${spent:.2f} ≈ {spent*7.2:.1f} 元")


if __name__ == "__main__":
    main()
