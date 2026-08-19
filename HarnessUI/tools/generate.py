#!/usr/bin/env python3
"""Batch runner: character manifest in, installable DSH skin packages out.

Per character it runs the whole loop — generate the light scene, generate the
night scene pinned to the same character with `--subject-ref`, strip the fake
signature image-01 stamps into the corner, then assemble the package. Each
stage is skipped when its artefact already exists, so a rerun after a failure
costs nothing and a single character can be re-rolled by deleting its art.

The composition contract in PROMPT is the part that matters. A skin is not a
wallpaper: the chat column, the composer and the sidebar sit on top of this
image, so the character has to stay inside the left third and the right two
thirds have to stay quiet. Backgrounds that ignore that read as noise behind
text no matter how good the art is.

Usage:
    python3 generate.py --manifest characters.json --art art --out out
    python3 generate.py --manifest characters.json --art art --out out --only ganyu
    python3 generate.py --manifest characters.json --art art --out out --dry-run
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import build_skin
from clean_art import scrub

# Composition contract shared by every character. `{look}` carries the
# character description, `{scene}` the setting, `{light}` the time of day.
PROMPT = (
    "anime game illustration, official splash art style. {look} "
    "Standing full-body on the FAR LEFT third of the frame, three-quarter view, "
    "the figure and all flowing hair kept inside the left 35% of the image. "
    "Setting: {scene}, {light}. "
    "The RIGHT TWO-THIRDS of the image is deliberately open and uncluttered: "
    "soft gradient sky, gentle atmospheric haze, very low detail, nothing to read, "
    "no props, no foreground objects. Clean negative space on the right. "
    "Cinematic wide composition. "
    "No text, no logo, no watermark, no signature, no user interface, no border."
)

LIGHT_SCENE = "bright daylight, warm rim light on the character"
DARK_SCENE = "deep night, moonlit, cool rim light on the character, lanterns glowing faintly"

WIDTH, HEIGHT = 2048, 1152


def run(command: list[str]) -> str:
    """Run one mmx invocation, returning stdout; raises on a non-zero exit."""
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"exit {result.returncode}: {result.stderr.strip()[:300]}")
    return result.stdout


def generate(entry: dict, art_dir: Path, *, dry_run: bool) -> None:
    """Produce `bg-light` and `bg-dark` for one character if missing."""
    art_dir.mkdir(parents=True, exist_ok=True)
    light = art_dir / "bg-light.jpg"
    dark = art_dir / "bg-dark.jpg"

    if not light.exists():
        prompt = PROMPT.format(look=entry["look"], scene=entry["scene"], light=LIGHT_SCENE)
        command = [
            "mmx", "image", "generate", "--prompt", prompt,
            "--width", str(WIDTH), "--height", str(HEIGHT),
            "--seed", str(entry.get("seed", 20260819)),
            "--out-dir", str(art_dir), "--out-prefix", "raw-light",
            "--quiet", "--non-interactive",
        ]
        if dry_run:
            print(f"    [dry-run] {' '.join(command[:6])} …")
        else:
            run(command)
            produced = sorted(art_dir.glob("raw-light*"))
            if not produced:
                raise RuntimeError("mmx produced no light image")
            produced[0].rename(light)
            scrub(light, 0.22, 0.11, backup=False)

    if not dark.exists():
        prompt = PROMPT.format(look=entry["look"], scene=entry["scene"], light=DARK_SCENE)
        command = [
            "mmx", "image", "generate", "--prompt", prompt,
            "--width", str(WIDTH), "--height", str(HEIGHT),
            "--seed", str(entry.get("seed", 20260819)),
            "--out-dir", str(art_dir), "--out-prefix", "raw-dark",
            "--quiet", "--non-interactive",
        ]
        # Pin the night scene to the character that came out of the day scene;
        # without this the two themes drift into two different people.
        if light.exists():
            command[3:3] = ["--subject-ref", f"type=character,image={light}"]
        if dry_run:
            print(f"    [dry-run] {' '.join(command[:6])} … (subject-ref)")
        else:
            run(command)
            produced = sorted(art_dir.glob("raw-dark*"))
            if not produced:
                raise RuntimeError("mmx produced no dark image")
            produced[0].rename(dark)
            scrub(dark, 0.22, 0.11, backup=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--art", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", action="append", help="build just these ids (repeatable)")
    parser.add_argument("--dry-run", action="store_true", help="print the mmx calls, generate nothing")
    args = parser.parse_args()

    if shutil.which("mmx") is None and not args.dry_run:
        sys.exit("mmx not on PATH — `npm install -g mmx-cli` then `mmx auth login`")

    entries = json.loads(args.manifest.read_text(encoding="utf-8"))
    if args.only:
        wanted = set(args.only)
        entries = [e for e in entries if e["id"] in wanted]
    args.out.mkdir(parents=True, exist_ok=True)

    print(f"共 {len(entries)} 个角色\n")
    ok = 0
    for index, entry in enumerate(entries, 1):
        name = f"{entry['id']} ({entry['name']})"
        print(f"[{index}/{len(entries)}] {name}")
        art_dir = args.art / entry["id"]
        try:
            generate(entry, art_dir, dry_run=args.dry_run)
            if args.dry_run:
                ok += 1
                continue
            skin = build_skin.Skin(**{k: v for k, v in entry.items() if k in build_skin.Skin.__dataclass_fields__})
            build_skin.build(skin, art_dir, args.out)
            ok += 1
        except (RuntimeError, FileNotFoundError, ValueError, KeyError) as error:
            print(f"  ✗ {error}")
    print(f"\n完成 {ok}/{len(entries)}")


if __name__ == "__main__":
    main()
