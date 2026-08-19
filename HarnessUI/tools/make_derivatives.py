#!/usr/bin/env python3
"""Build the display-sized WebP the skin actually swaps at runtime.

The delivered master is a 3840x2160 PNG of 6-8MB. Handing that to
`background-image` on every switch is what makes a picker feel broken: the
browser has to fetch and decode megabytes before the old frame is replaced, so
the window flashes or stalls. DSH's own window is ~1456pt wide, 2912px on this
Retina display, so anything past ~2560px wide is invisible detail bought with
latency.

Two derivatives per master:
    display/  2560x1440 WebP q82   — what the skin sets as the background
    thumb/     384x216  WebP q75   — what the gallery picker shows in its grid

Masters are never modified; delivery and acceptance still run on them.

Usage:
    python3 make_derivatives.py --src …/run/output --out …/run/skin-assets
"""

from __future__ import annotations

import argparse
import concurrent.futures
import pathlib
import sys

from PIL import Image

DISPLAY = (2560, 1440)
THUMB = (384, 216)


def build(master: pathlib.Path, src: pathlib.Path, out: pathlib.Path) -> tuple[str, int, int]:
    rel = master.relative_to(src)
    display = out / "display" / rel.with_suffix(".webp")
    thumb = out / "thumb" / rel.with_suffix(".webp")
    if display.exists() and thumb.exists():
        return (str(rel), display.stat().st_size, thumb.stat().st_size)
    with Image.open(master) as image:
        image = image.convert("RGB")
        display.parent.mkdir(parents=True, exist_ok=True)
        thumb.parent.mkdir(parents=True, exist_ok=True)
        image.resize(DISPLAY, Image.LANCZOS).save(display, "WEBP", quality=82, method=5)
        image.resize(THUMB, Image.LANCZOS).save(thumb, "WEBP", quality=75, method=5)
    return (str(rel), display.stat().st_size, thumb.stat().st_size)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--jobs", type=int, default=6)
    args = parser.parse_args()

    masters = [p for p in sorted(args.src.rglob("*.png")) if "reject" not in p.name]
    if not masters:
        sys.exit("没有找到成品 PNG")
    done = big = small = 0
    with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        for _, d, t in pool.map(lambda m: build(m, args.src, args.out), masters):
            done += 1
            big += d
            small += t
            if done % 100 == 0:
                print(f"  {done}/{len(masters)}")
    print(f"完成 {done} 组 · display 合计 {big/1048576:.0f}MB（均 {big/done/1024:.0f}KB）"
          f" · thumb 合计 {small/1048576:.1f}MB（均 {small/done/1024:.0f}KB）")


if __name__ == "__main__":
    main()
