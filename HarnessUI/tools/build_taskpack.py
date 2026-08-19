#!/usr/bin/env python3
"""Assemble the generation task pack handed to MiniMax Design.

One entry per character-variant (default look plus every alternate outfit), each
carrying the prompt, the negative prompt, and a downscaled copy of the official
art that anchors the character's identity.

The anchor is the reason this pack exists. Text-only generation produces a
plausible anime girl rather than the specific character — verified here on
2026-08-19 with a 200-word description that got the composition right and the
character wrong. So the prompt deliberately does NOT describe the character:
it describes composition, scene, light and style, and leaves identity entirely
to the reference image.

Anchors are re-encoded to 1280px JPEG. Full-resolution art would put the pack
near a gigabyte, which is not a handoff — it's a migration.

Usage:
    python3 build_taskpack.py --library "/Volumes/share/…/HarnessUI" \\
        --rosters ../research --out /tmp/taskpack
"""

from __future__ import annotations

import argparse
import io
import json
import shutil
from pathlib import Path

from PIL import Image

# Raised from 1600 once native-resolution sources landed. Identity in this
# pipeline comes only from the anchor, so anchor detail is the one place where
# spending pack size buys quality directly. 297 anchors at this size is ~150MB,
# which is still a handoff.
ANCHOR_PX = 2048
ANCHOR_QUALITY = 88

# Scene pools per game. Deliberately generic: the anchor fixes who the character
# is, so the prompt only has to fix where they stand and how it is lit — and a
# named region would fight anchors for characters from elsewhere in the game.
# Scene pools. The first pass shipped a "wide street, neon signage, glass
# towers" pool for Zenless and got back a concrete lot with a city skyline, and
# a ruined-city night for Star Rail — both rejected on sight. Cities, ruins and
# wasteland are out across the board; these pools stay on water, sky, garden and
# soft interiors, which is also where the reference material the brief was built
# from lives.
SCENES = {
    "genshin": "an open natural vista — calm sea or lake at golden hour, distant soft hills, "
               "drifting petals, warm hazy sky",
    "hsr": "an open dreamlike vista — luminous sky, drifting light motes, distant soft "
           "silhouettes far out of focus, no hard structures",
    "zzz": "an open seaside or garden scene — water, soft greenery, warm sky, no buildings",
}

# Never allow these, regardless of game. Each was produced and rejected in the
# first pilot round.
BANNED_SCENERY = (
    "wasteland, ruins, rubble, debris, concrete lot, construction site, industrial yard, "
    "modern city, city skyline, skyscrapers, office buildings, streets, traffic, "
    "cyberpunk alley, neon signage, dystopia, post-apocalyptic"
)

PROMPT = (
    "Anime illustration in official game splash-art quality, matching the reference image's "
    "character design exactly — same hair colour, eye colour, outfit colours, accessories and "
    "silhouette. {subject} "
    "POSE AND STYLE: an elegant, relaxed standing pose — poised and alluring rather than "
    "mid-action. Favour a graceful figure, visible legs, sheer black or patterned tights / "
    "stockings / thighhighs where the design allows, and an open, skin-revealing silhouette. "
    "Avoid bulky armour, heavy coats, full-length trousers and combat action poses. "
    "COMPOSITION (strict): the character stands full-body in the LEFT THIRD of a 16:9 frame; "
    "the figure and ALL flowing hair, skirt, weapon and effects stay inside the left 35% of the "
    "image. The RIGHT 65% is deliberately empty: {scene}, rendered low-detail, low-contrast, "
    "atmospheric and out of focus, with nothing readable in it. Nothing occupies the bottom "
    "centre of the frame. The character faces the viewer or looks right, never away. "
    "LIGHT: {light}. "
    "Clean rendering, correct anatomy, five fingers per hand, symmetrical features, "
    "crisp linework, no compression artefacts."
)

NEGATIVE = (
    "text, letters, caption, subtitle, title, logo, watermark, artist signature, stamp, "
    "QR code, UI, interface, border, frame, "
    "wasteland, ruins, rubble, concrete lot, construction site, modern city, city skyline, "
    "skyscrapers, buildings, streets, cyberpunk alley, neon signage, post-apocalyptic, "
    "underexposed, crushed blacks, silhouette-only character, character lost in shadow, "
    "bulky armour, heavy coat, full-length trousers, mid-action combat pose, "
    "character centred, character on the right, hair crossing the centre of the frame, "
    "busy background, architectural detail on the right, foreground objects, "
    "extra fingers, missing fingers, fused fingers, deformed hands, extra limbs, "
    "malformed face, asymmetric eyes, blurry face, "
    "3d render, cgi, photo, live action, animation frame, video"
)

LIGHT = {
    "light": "bright daylight, warm key light with a soft rim on the character, high overall "
             "brightness, clear sky",
    # The first round asked for "low overall brightness" and got images at 0.12-0.23 mean
    # luminance — technically a night scene, visually unusable as a backplate. The dark
    # variant is an evening mood, not an unlit one: the character stays clearly lit and the
    # scene stays readable.
    "dark": "evening or twilight — deep blue and violet sky, moonlight or warm lantern glow. "
            "The CHARACTER REMAINS CLEARLY LIT AND FULLY VISIBLE, lit by a strong warm key "
            "light plus a cool rim; the scene is still easy to read. Moody, not black. "
            "Same location, same outfit and same character as the day version — only the "
            "time of day changes. Overall brightness moderate, never crushed to darkness.",
}


def best_anchor(refs: Path) -> Path | None:
    """The largest available anchor for a character, by pixel area.

    Both `portrait.png` (the wiki's nominated page image) and `splash.png`
    (the named full-art file) are candidates, and which one is better varies
    per character: measured across a sample, the page image won 3 times, the
    splash art once, and they were the same file twice — the splash is often a
    wide crop where the page image is a taller full-body shot. Picking by area
    beats preferring either one by name.
    """
    candidates = []
    # ONLY the classes that are guaranteed to be this character's own full art.
    #
    # An earlier version also drew from the gallery `style` and `detail`
    # folders, to lift the 37 anchors whose page image had a short edge under
    # 1000px. That was a bad trade and an audit caught it: 128 of 168 default
    # anchors ended up sourced from those folders, and the picks included
    # `furina-birthday-2024-shorts.png` standing in for Clorinde and
    # `kaeya-birthday-2025-shorts.png` — a male character — standing in for
    # Dahlia, plus a pile of chibi birthday art. The gallery classes are
    # per-character *collections*, not per-character *portraits*: the collector
    # fills leftover quota with shared promo art, so a high-resolution file in
    # there is not necessarily this character at all.
    #
    # A sharp image of the wrong character is far worse than a soft image of
    # the right one, so resolution loses to provenance here.
    # hires.png first: it is the game's native full-body art fetched losslessly
    # (`?format=original`), typically 5-20x the pixels of the page image and
    # without the CDN's WebP transcode. portrait/splash remain the fallback for
    # the characters whose wiki has no Portrait.png yet.
    for path in (refs / "hires.png", refs / "portrait.png", refs / "splash.png"):
        if not path.exists():
            continue
        try:
            with Image.open(path) as image:
                width, height = image.size
        except Exception:
            continue
        upright = width <= height * 1.3
        candidates.append(((1 if upright else 0), width * height, path))
    return max(candidates)[2] if candidates else None


def encode_anchor(source: Path, target: Path) -> int:
    """Downscale one anchor into the pack; returns bytes written."""
    with Image.open(source) as image:
        rgb = image.convert("RGB")
        rgb.thumbnail((ANCHOR_PX, ANCHOR_PX), Image.LANCZOS)
        buffer = io.BytesIO()
        rgb.save(buffer, "JPEG", quality=ANCHOR_QUALITY, optimize=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(buffer.getvalue())
    return len(buffer.getvalue())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--rosters", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--games", nargs="*", default=["genshin", "hsr", "zzz"])
    args = parser.parse_args()

    anchors_dir = args.out / "anchors"
    tasks: list[dict] = []
    packed = skipped = 0
    total_bytes = 0

    for game in args.games:
        roster = json.loads((args.rosters / f"roster-{game}.json").read_text(encoding="utf-8"))
        game_zh = roster["game_zh"]
        for character in roster["characters"]:
            refs = args.library / game_zh / character["id"] / "refs"
            portrait = best_anchor(refs)
            if portrait is None:
                skipped += 1
                continue

            variants = [("default", portrait, "Default outfit.")]
            ledger = refs / "outfits.json"
            if ledger.exists():
                for entry in json.loads(ledger.read_text(encoding="utf-8")).get("outfits", []):
                    art = refs / "outfits" / entry["file"]
                    if art.exists():
                        variants.append((art.stem, art, f'Alternate outfit "{entry["outfit"]}".'))

            for variant_id, art_path, subject in variants:
                rel = Path(game) / character["id"] / f"{variant_id}.jpg"
                total_bytes += encode_anchor(art_path, anchors_dir / rel)
                packed += 1
                tasks.append({
                    "id": f"{game}/{character['id']}/{variant_id}",
                    "game": game,
                    "game_zh": game_zh,
                    "character": character["id"],
                    "character_name": character["name_en"],
                    "variant": variant_id,
                    "anchor": f"anchors/{rel.as_posix()}",
                    "outputs": {
                        side: {
                            "file": f"output/{game}/{character['id']}/{variant_id}/{side}.png",
                            "prompt": PROMPT.format(subject=subject, scene=SCENES[game],
                                                    light=LIGHT[side]),
                        } for side in ("light", "dark")
                    },
                    "negative_prompt": NEGATIVE,
                    "banned_scenery": BANNED_SCENERY,
                    "aspect_ratio": "16:9",
                    "min_width": 2048,
                })

    manifest = {
        "pack": "HarnessUI-skin-backplates",
        "version": "1.0.0",
        "built": "2026-08-19",
        "deliverable": "2D static 16:9 skin backplates, light + dark per variant",
        "task_count": len(tasks),
        "image_count": len(tasks) * 2,
        "characters": len({t["character"] for t in tasks}),
        "anchor_note": "每条任务必须把 anchor 作为角色参考图输入；prompt 不描述角色外观，身份完全由 anchor 决定。",
        "read_first": ["docs/SPEC.md", "docs/ACCEPTANCE.md"],
        "tasks": tasks,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"任务 {len(tasks)} 条 · 出图 {len(tasks) * 2} 张 · 角色 {manifest['characters']} 个")
    print(f"锚图 {packed} 张 · {total_bytes / 1048576:.1f} MB · 跳过无素材角色 {skipped}")


if __name__ == "__main__":
    main()
