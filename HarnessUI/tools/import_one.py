#!/usr/bin/env python3
"""把一张外部图片收进素材库。

菜单栏控制器负责挑文件，真正的缩放交给这里 —— Electron 的 nativeImage 不会编
WebP，而整个库都是 WebP，混进 PNG 会让同一个画廊里一半图大十倍。

一张图进来要落两份：display（3840x2160，皮肤实际铺的那张）和 thumb（384x216，
画廊网格用）。不是 16:9 的先按 cover 裁 —— 皮肤是全窗铺底，比例不对会被拉变形。

Usage:
    python3 import_one.py --src <图片> --id <game/character/variant> --side light|dark
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path.home() / ".harness-ui"
DISPLAY = (3840, 2160)
THUMB = (384, 216)


def cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """按 cover 裁到目标比例再缩放，绝不拉伸。"""
    tw, th = size
    sw, sh = image.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    resized = image.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    return resized.crop((left, top, left + tw, top + th))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=pathlib.Path, required=True)
    parser.add_argument("--id", required=True, help="game/character/variant")
    parser.add_argument("--side", default="light", choices=("light", "dark"))
    args = parser.parse_args()

    parts = args.id.split("/")
    if len(parts) != 3:
        sys.exit("id 必须是 game/character/variant 三段")

    with Image.open(args.src) as image:
        image = image.convert("RGB")
        for root, size, quality in (("display", DISPLAY, 88), ("thumb", THUMB, 75)):
            target = ROOT / root / args.id / f"{args.side}.webp"
            target.parent.mkdir(parents=True, exist_ok=True)
            cover(image, size).save(target, "WEBP", quality=quality, method=5)

    print(json.dumps({"ok": True, "id": args.id, "side": args.side}, ensure_ascii=False))


if __name__ == "__main__":
    main()
