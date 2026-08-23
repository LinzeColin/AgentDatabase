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
import concurrent.futures
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
    # 鸣潮的官方美术偏东方山水与云海，沿用「水 / 天 / 园」的同一条线，
    # 但换成竹林、云海、远山，避免和原神的金色海岸撞。
    "wuwa": "an open eastern landscape — drifting cloud sea over distant blue mountains, "
            "bamboo or willow far out of focus, clear luminous sky, no structures",
    # 异环是现代都市异能题材，但「现代都市」正好是被禁的背景（BANNED_SCENERY），
    # 所以取它世界观里不含建筑的那一半：海滨与公园的开阔处。
    "nte": "an open waterside park at dusk — calm harbour water, distant soft treeline, "
           "drifting light haze and scattered petals, wide gradient sky, no buildings",
    # 崩坏3 的官方美术是近未来科幻，但科幻都市与废墟正好在 BANNED_SCENERY 里，
    # 所以取它世界观里开阔干净的那一半：海湾、长空、落樱，也避开和前四作撞色。
    "hi3": "an open seaside vista under a vast clear sky — calm bay water, drifting cherry "
           "blossom petals, distant soft horizon, luminous haze, no structures",
}

# Never allow these, regardless of game. Each was produced and rejected in the
# first pilot round.
BANNED_SCENERY = (
    "wasteland, ruins, rubble, debris, concrete lot, construction site, industrial yard, "
    "modern city, city skyline, skyscrapers, office buildings, streets, traffic, "
    "cyberpunk alley, neon signage, dystopia, post-apocalyptic"
)

WARDROBE_DEFAULT = (
    # v1.7：身份照锚图，服装按丝袜/pin-up 规则；冲突时显式以规则为准。
    "MANDATORY WARDROBE AND PRESENTATION — this is glamour pin-up art and the wardrobe rule "
    "is not optional: {hosiery} on fully visible legs, worn with visible garter straps. "
    "Where the canonical design has trousers, greaves or armoured legs, restyle the legwear "
    "into {hosiery} while keeping that design's own colours, patterns and trim. The silhouette is maximally skin-revealing: bare shoulders, "
    "bare arms, bare midriff, fully bare thighs above the stocking band, and a deep plunging "
    "neckline. Favour high-cut leotard, micro-skirt, bodysuit and open-side silhouettes over "
    "anything that covers the hips or waist. "
    "PIN-UP DIRECTION: emphasise the unbroken leg line from hip to ankle and the bust line; "
    "the pose is consciously alluring and suggestive — weight on one hip, arched back, chin "
    "slightly lowered, direct eye contact with the viewer. "
    "PRECEDENCE: character IDENTITY (face, hair colour and style, eye colour, signature "
    "accessories, colour palette) matches the reference exactly; WARDROBE STYLING follows "
    "this paragraph and overrides the reference wherever the two conflict. "
    "Avoid bulky armour, heavy coats, full-length trousers and combat action poses. "
)

WARDROBE_CANONICAL = (
    # v1.9.1 起不再使用（R5 豁免取消，全员 pin-up 阶梯）；保留供旧包核对。
    "WARDROBE (strict): reproduce the canonical outfit in the reference image exactly, "
    "including its garments, coverage, colours, patterns, accessories and silhouette. Do not "
    "restyle, remove or add clothing, and do not make the outfit more revealing. "
    "PRECEDENCE: character IDENTITY (face, hair colour and style, eye colour, signature "
    "accessories, colour palette) and WARDROBE both match the reference exactly. "
)

# v1.9.2（2026-08-23 用户反馈）：爱莉希雅一批成品「腿型过胖」。根因是 L5 措辞里
# PIN-UP DIRECTION 的 "emphasise the unbroken leg line from hip to ankle" 在降级到
# L4/L3 时仍保留，放大腿部曲线；叠加部分锚图是低清，锁不住角色的纤细体型。
# 正解是加一条独立 PHYSIQUE 条款，明确身体比例必须跟锚图（尤其是细腰窄胯长细腿），
# 不许加粗拉宽。注意：本条款是整段独立文本，措辞绝不能与 erotic_levels.py 的任何
# 替换串（SUGGESTIVE/NO_SUGGEST/NO_ARCH/MAXIMAL/MODEST/PIN-UP DIRECTION 等）字节级
# 重叠，否则阶梯降级会漏改或误改它。已核对：全段不含任何被替换子串。
PHYSIQUE = (
    "PHYSIQUE (strict): the figure's body proportions follow the reference character's actual "
    "slender build exactly — narrow hips, slim waist, long slim thighs and calves; legs and "
    "hips are never thickened, widened or exaggerated; keep the hip-to-thigh-to-calf ratio and "
    "limb slenderness as in the reference image. The pose may be alluring, but limbs and frame "
    "stay natural, undistorted and in proportion. "
)

PROMPT = (
    "Anime illustration in official game splash-art quality, matching the reference image's "
    "character design exactly — same hair colour, eye colour, outfit colours, accessories and "
    "silhouette. {subject} "
    "POSE AND STYLE: an elegant, relaxed standing pose — poised and alluring rather than "
    "mid-action. "
    "{wardrobe}"
    "{physique}"
    "COMPOSITION (strict): the character stands full-body in the LEFT THIRD of a 16:9 frame; "
    "the figure and ALL flowing hair, skirt, weapon and effects stay inside the left 35% of the "
    "image. The RIGHT 65% is deliberately empty: {scene}, rendered low-detail, low-contrast, "
    "atmospheric and out of focus, with nothing readable in it. Nothing occupies the bottom "
    # 用户点名「避免这种姿势」：指的是背对/侧转到能看见后背的姿势。
    # 普罗米娅那四张返工两轮都还在转身，所以改成显式禁止，不再靠「never away」这种弱措辞。
    "centre of the frame. "
    "ORIENTATION (hard rule): the character faces the viewer squarely — chest, hips and face "
    "all oriented toward the camera within about 30 degrees of frontal. NEVER show the "
    "character's back, spine, shoulder blades or rear; no turned-away pose, no "
    "over-the-shoulder glance, no three-quarter-rear view. Head and torso face the same way: "
    "the difference between where the face looks and where the chest points must not exceed "
    "a natural head turn of about 45 degrees. "
    "LIGHT: {light}. "
    "Clean rendering, correct anatomy, five fingers per hand, symmetrical features, "
    "crisp linework, no compression artefacts. "
    # gpt-image-2 没有 negative_prompt 参数。v1.5 把禁止项放在任务包的
    # negative_prompt 字段里，字段发不出去 —— 594 条 prompt 正文里
    # "chibi" 出现 0 次，直到成品出来才发现。禁止项必须写进正文。
    "EXCLUDE — none of the following may appear: {excluded}."
)

EXCLUDED = (
    "chibi, super-deformed or child-like proportions, oversized head, doll or figurine look, "
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


def load_hosiery(rosters: Path) -> dict:
    """丝袜配置。缺文件就退回黑丝——行为和改这版之前一致，不会突然变。"""
    try:
        return json.loads((rosters / "hosiery.json").read_text(encoding="utf-8"))
    except Exception:
        return {"types": {"black_sheer": {"prompt": "sheer black stockings"}},
                "overrides": {}}


def hosiery_for(cfg: dict, game: str, character: dict, anchor: Path) -> tuple[str, str]:
    """返回 (类型 key, prompt 措辞)。三层：硬约束 → 用户覆写 → 按配色推断。"""
    types = cfg.get("types", {})
    def phrase(key):
        return key, types.get(key, {}).get("prompt", "sheer black stockings")
    # ① 硬约束：幼态体型照原设，不加任何丝袜条款
    if character.get("r5"):
        return phrase("canonical")
    # ② 用户逐角色覆写——他比任何规则准
    key = (cfg.get("overrides") or {}).get(f"{game}/{character['id']}")
    if key:
        return phrase(key)
    # ③ 按锚图腿部区域的主导色相兜底推断。
    #    注意：这一层是按配色协调推的，**不是按市场热度实测的**。
    try:
        import colorsys
        with Image.open(anchor) as image:
            rgb = image.convert("RGB")
            # 只取水平中段：锚图两侧是背景，全宽取样会把背景色当成服装色
            # （夜兰站在亮水面上，第一版因此被判成白丝）。
            leg = rgb.crop((int(rgb.width * 0.25), int(rgb.height * 0.62),
                            int(rgb.width * 0.75), rgb.height)).resize((40, 24))
            px = list(leg.getdata())
        hues, light, counted = [], 0, 0
        for r, g, b in px:
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if v > 0.93 and s < 0.10:
                continue                      # 近白/近透明：锚图背景，不算数
            counted += 1
            if v > 0.72 and s < 0.30:
                light += 1
            elif s > 0.25:
                hues.append(h)
        if counted and light > counted * 0.45:
            return phrase("white_opaque")          # 白/浅/圣洁系 → 白丝
        if hues:
            hues.sort()
            h = hues[len(hues) // 2]
            if 0.55 < h < 0.85:
                return phrase("black_sheer")       # 蓝紫/哥特 → 黑丝
            if h < 0.10 or h > 0.92:
                return phrase("black_sheer")       # 红橙暖色 → 黑丝（高对比）
    except Exception:
        pass
    return phrase("black_sheer")


def pathlib_stem(name: str) -> str:
    return name.rsplit(".", 1)[0] if "." in name else name


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
        # 崩坏3 官网立绘是透明底 PNG，直接 convert("RGB") 透明区会变纯黑，
        # 锚图带黑底会把生成往暗背景带。有 alpha 一律先垫白底。
        if image.mode in ("RGBA", "LA", "PA") or (image.mode == "P" and "transparency" in image.info):
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.split()[3])
            rgb = background
        else:
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
    parser.add_argument("--games", nargs="*", default=["genshin", "hsr", "zzz", "wuwa"])
    parser.add_argument("--version", default="1.8.0")
    parser.add_argument("--built", default="2026-08-20")
    parser.add_argument("--only", nargs="*", help="只打包这些 <game>/<character>")
    args = parser.parse_args()

    hosiery_cfg = load_hosiery(args.rosters)
    anchors_dir = args.out / "anchors"
    tasks: list[dict] = []
    jobs: list[tuple] = []
    packed = skipped = 0
    total_bytes = 0

    for game in args.games:
        roster = json.loads((args.rosters / f"roster-{game}.json").read_text(encoding="utf-8"))
        game_zh = roster["game_zh"]
        for character in roster["characters"]:
            if args.only and f"{game}/{character['id']}" not in args.only:
                continue
            refs = args.library / game_zh / character["id"] / "refs"
            portrait = best_anchor(refs)
            if portrait is None:
                skipped += 1
                continue

            # 幼态体型角色一律走 canonical：照原设服装出，不加 pin-up、不加露肤。
            # v1.9.1 曾把这条豁免取消（"全员进 pin-up 阶梯"），而 r5 字段在花名册里
            # 一个都没标过——豁免既没数据也没逻辑。2026-08-23 试跑里瑶瑶被做得比原设
            # 更露，就是这么来的。这条不是可配置项。
            wardrobe = WARDROBE_CANONICAL if character.get("r5") else WARDROBE_DEFAULT

            variants = [("default", portrait, "Default outfit.")]
            ledger = refs / "outfits.json"
            titled: dict = {}
            skip_portrait: set = set()
            if ledger.exists():
                for entry in json.loads(ledger.read_text(encoding="utf-8")).get("outfits", []):
                    stem = pathlib_stem(entry.get("file", ""))
                    titled[stem] = entry.get("outfit", stem)
                    # is_portrait：这张图同时是 refs 根的 portrait.png（hi3 每套装甲
                    # 各是一张立绘，代表装甲兼作 portrait），跳过以免同图出两条任务。
                    if entry.get("is_portrait"):
                        skip_portrait.add(stem)
            # 以**目录**为准，不以台账为准：台账会落后于磁盘。
            # 实测 jane/hidden-nightfade、astra/scarlet-rock、nilou/neither-flower-nor-mist
            # 三张 PNG 都在，台账没记，任务包就把它们漏了。
            outfit_dir = refs / "outfits"
            if outfit_dir.is_dir():
                for art in sorted(outfit_dir.iterdir()):
                    if art.suffix.lower() != ".png" or art.name.startswith("._"):
                        continue
                    if art.stem in skip_portrait:
                        continue
                    label = titled.get(art.stem, art.stem.replace("-", " ").title())
                    variants.append((art.stem, art, f'Alternate outfit "{label}".'))

            for variant_id, art_path, subject in variants:
                hos_key, hos_phrase = hosiery_for(hosiery_cfg, game, character, art_path)
                rel = Path(game) / character["id"] / f"{variant_id}.jpg"
                # 编码排队，最后并发跑：这一步是纯网络 IO，串行时 8 张要 2 分钟
                jobs.append((art_path, anchors_dir / rel))
                packed += 1
                tasks.append({
                    "id": f"{game}/{character['id']}/{variant_id}",
                    "game": game,
                    "game_zh": game_zh,
                    "character": character["id"],
                    "character_name": character["name_en"],
                    "name_zh": character.get("name_zh"),
                    "r5": character.get("r5"),
                    "hosiery": hos_key,
                    "variant": variant_id,
                    "anchor": f"anchors/{rel.as_posix()}",
                    "outputs": {
                        side: {
                            "file": f"output/{game}/{character['id']}/{variant_id}/{side}.png",
                            "prompt": PROMPT.format(subject=subject, scene=SCENES[game],
                                                    light=LIGHT[side], excluded=EXCLUDED,
                                                    wardrobe=wardrobe.format(hosiery=hos_phrase)
                                                        if "{hosiery}" in wardrobe else wardrobe,
                                                    physique=PHYSIQUE),
                        } for side in ("light", "dark")
                    },
                    "banned_scenery": BANNED_SCENERY,
                    "aspect_ratio": "16:9",
                    "min_width": 2048,
                })

    print(f"锚图编码中：{len(jobs)} 张（并发 12）…", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for n, size in enumerate(pool.map(lambda j: encode_anchor(*j), jobs), 1):
            total_bytes += size
            if n % 50 == 0:
                print(f"  {n}/{len(jobs)}", flush=True)

    # decisions 块需要的事实：r5 标注角色、官网无图装甲、无官方高清图的皮肤变体，
    # 都在构建时从花名册 + 素材库实测，不手填。
    r5_characters = []
    suits_no_art = []
    skins_no_art = []
    for game in args.games:
        roster = json.loads((args.rosters / f"roster-{game}.json").read_text(encoding="utf-8"))
        for character in roster["characters"]:
            if args.only and f"{game}/{character['id']}" not in args.only:
                continue
            if character.get("r5"):
                r5_characters.append(
                    f"{character['id']}（{character.get('name_zh') or character['name_en']}，{character['r5']}）")
            ledger_path = args.library / roster["game_zh"] / character["id"] / "refs" / "outfits.json"
            ledger = set()
            if ledger_path.exists():
                ledger = {e["outfit"] for e in
                          json.loads(ledger_path.read_text(encoding="utf-8")).get("outfits", [])}
            for suit in character.get("battlesuits", []):
                if suit["name_en"] not in ledger:
                    suits_no_art.append(f"{character['id']} :: {suit['name_en']}")
                for outfit in suit.get("outfits", []):
                    if not outfit.endswith("/Outfit") and outfit not in ledger:
                        skins_no_art.append(f"{character['id']} :: {suit['name_en']} :: {outfit}")

    manifest = {
        "pack": "HarnessUI-skin-backplates",
        "version": args.version,
        "built": args.built,
        "deliverable": "2D static 16:9 skin backplates, light + dark per variant",
        "task_count": len(tasks),
        "image_count": len(tasks) * 2,
        "characters": len({t["character"] for t in tasks}),
        "anchor_note": "每条任务必须把 anchor 作为角色参考图输入；prompt 不描述角色外观，身份完全由 anchor 决定。",
        "read_first": ["docs/SPEC.md", "docs/ACCEPTANCE.md"],
        "decisions": {
            "date": "2026-08-23",
            "r5_pinup_for_all": {
                "decision": "R5 豁免取消：全部角色（含下列 12 名 r5 标注角色）都进 pin-up 阶梯；"
                            "任务包统一存 L5 措辞，运行时按 L4→L3→L2 降级，L2 出不来标 blocked 不降 L1。",
                "decided_by": "用户",
                "r5_characters": r5_characters,
            },
            "skin_variants_pending_phase2": {
                "decision": "非默认服装变体（皮肤）官网无高清立绘，本版不进任务包，待二期从 Fandom 等来源补锚。",
                "count": len(skins_no_art),
                "items": skins_no_art,
            },
            "suits_without_official_art": {
                "decision": "下列装甲官网内容接口无立绘，本版无锚图不进任务包，待补锚后补跑。",
                "count": len(suits_no_art),
                "items": suits_no_art,
            },
            "physique_fix_v1.9.2": {
                "date": "2026-08-23",
                "decision": "用户反馈爱莉希雅成品腿型过胖：根因是 L5 措辞 PIN-UP DIRECTION 的"
                            "「emphasise the unbroken leg line from hip to ankle」在降级到 L4/L3 时"
                            "仍保留，放大腿部曲线。本版全任务 prompt 新增独立 PHYSIQUE 条款"
                            "（细腰窄胯长细腿、比例严格照锚图、不许加粗拉宽），不参与 erotic_levels.py "
                            "任何替换串；Elysia 锚图 default/miss-pink 换官方高清 miss-pink-elf.jpg。",
            },
        },
        "tasks": tasks,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"任务 {len(tasks)} 条 · 出图 {len(tasks) * 2} 张 · 角色 {manifest['characters']} 个")
    print(f"锚图 {packed} 张 · {total_bytes / 1048576:.1f} MB · 跳过无素材角色 {skipped}")


if __name__ == "__main__":
    main()
