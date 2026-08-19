#!/usr/bin/env python3
"""Strip the fake artist signature image-01 stamps into the bottom-right corner.

The model adds one on most generations regardless of "no watermark, no
signature" in the prompt, so this is a batch concern rather than a per-image
touch-up. The corner it lands in is always low-detail scenery (that is the
whole point of the skin composition brief), so cloning a neighbouring band of
the same image over it is invisible — no inpainting model needed.

Usage:
    python3 clean_art.py art/ganyu/bg-light.jpg            # in place, .bak kept
    python3 clean_art.py art/*/*.jpg --width 0.22 --height 0.06
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

try:
    from PIL import Image, ImageFilter
except ImportError:  # pragma: no cover - environment guard
    sys.exit("Pillow is required: python3 -m pip install Pillow")


DONOR_GAP = 3
"""Patch-heights of clearance between the corner and the donor band."""


def scrub(path: Path, width_frac: float, height_frac: float, *, backup: bool) -> tuple[int, int]:
    """Clone-patch the bottom-right corner of one image.

    The replacement band is taken from ABOVE the corner rather than beside it:
    these compositions are horizon-based, so pixels at the same height carry
    the same gradient, while pixels to the left may cross a shoreline or
    reflection edge. The patch is mirrored vertically so the seam lands on
    matching tones, then feathered with a slight blur.

    The donor is lifted a full `DONOR_GAP` patch-heights clear of the corner.
    Sampling the band immediately above (the obvious choice) fails: the
    signature image-01 stamps is two lines tall, so that band still contains
    the upper line and the "cleaned" image just gets the watermark pasted
    back — observed on the first run here.

    @param path - image to clean, rewritten in place.
    @param width_frac - corner width as a fraction of image width.
    @param height_frac - corner height as a fraction of image height.
    @param backup - keep the original alongside as `<name>.orig<ext>`.
    @returns the patched region size in pixels.
    """
    if backup:
        original = path.with_name(path.stem + ".orig" + path.suffix)
        if not original.exists():
            shutil.copyfile(path, original)

    with Image.open(path) as source:
        image = source.convert("RGB")
        w, h = image.size
        pw, ph = int(w * width_frac), int(h * height_frac)
        box = (w - pw, h - ph, w, h)

        top = max(0, h - ph * (DONOR_GAP + 1))
        donor = image.crop((w - pw, top, w, top + ph)).transpose(Image.FLIP_TOP_BOTTOM)
        donor = donor.filter(ImageFilter.GaussianBlur(1.2))

        # Feather the top edge so the seam is not a hard line.
        mask = Image.new("L", (pw, ph), 255)
        for y in range(min(ph, 24)):
            for_row = int(255 * (y / 24))
            mask.paste(for_row, (0, y, pw, y + 1))

        image.paste(donor, box[:2], mask)
        image.save(path, quality=95)
    return pw, ph


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--width", type=float, default=0.22, help="corner width fraction")
    parser.add_argument("--height", type=float, default=0.11, help="corner height fraction")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    for path in args.images:
        if not path.is_file():
            print(f"  ✗ {path} 不存在")
            continue
        pw, ph = scrub(path, args.width, args.height, backup=not args.no_backup)
        print(f"  ✓ {path.name:<24} 覆盖右下角 {pw}×{ph}px")


if __name__ == "__main__":
    main()
