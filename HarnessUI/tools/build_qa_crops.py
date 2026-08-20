#!/usr/bin/env python3
"""裁出人物特写，供人工扫查解剖缺陷。

自动判官试了三轮都没能复现用户的判断：宽松版漏掉他亲自否掉的那张，
严格版把 100 张里的 83 张全报成缺陷，改成打"显眼度"分之后又把那张打成 3 分放行。
再调下去就是拿用户的时间赌下一次能猜中。

人眼扫一面缩略图墙是几分钟的事，而且判断标准就是他本人，不需要近似。
所以这里只做机器该做的那部分：把人物从 16:9 的画幅里裁出来放大。
整图缩略里人物只占左 35%，手指级别的缺陷根本看不见；裁出来之后同样的
缩略图尺寸能给到三倍的人物像素。

Usage:
    python3 build_qa_crops.py --catalog … --out …/qa/crops
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import pathlib

from PIL import Image

CROP = 0.42
WIDTH = 460


def one(entry: dict, root: pathlib.Path, out: pathlib.Path, side: str) -> str | None:
    master = root / "master" / entry["id"] / f"{side}.png"
    if not master.exists():
        return None
    target = out / entry["id"] / f"{side}.webp"
    if target.exists():
        return str(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(master) as image:
        image = image.convert("RGB")
        w, h = image.size
        region = image.crop((0, 0, int(w * CROP), h))
        scale = WIDTH / region.size[0]
        region.resize((WIDTH, int(region.size[1] * scale)), Image.LANCZOS).save(
            target, "WEBP", quality=84, method=4)
    return str(target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=pathlib.Path, required=True)
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path.home() / ".harness-ui")
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args()

    entries = json.loads(args.catalog.read_text(encoding="utf-8"))["entries"]
    jobs = [(e, s) for e in entries for s in ("light", "dark")]
    made = 0
    with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        for result in pool.map(lambda js: one(js[0], args.root, args.out, js[1]), jobs):
            if result:
                made += 1
    size = sum(f.stat().st_size for f in args.out.rglob("*.webp"))
    print(f"人物特写 {made} 张 · {size/1048576:.0f}MB → {args.out}")


if __name__ == "__main__":
    main()
