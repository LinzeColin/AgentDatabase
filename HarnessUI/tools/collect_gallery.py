#!/usr/bin/env python3
"""Collect the remaining official art classes from each character's gallery.

`collect_refs.py` takes the default portrait and `collect_outfits.py` the
alternate outfits. A character's `/Gallery` page holds far more — Ganyu's has
325 files — but most of it is worthless for generation: element icons, item
sprites, video links, holiday greeting cards, brand collaborations. Grabbing
the page wholesale would add gigabytes of greeting cards and bury the art that
matters.

So the gallery is classified rather than mirrored:

    A  anchor      wish / outfit splash art          (already collected)
    B  style       official wallpapers, promo art    ← collected here
    C  detail      constellation, skill, sticker art ← collected here
    D  noise       icons, UI, video links, ads       ← skipped

Class B carries the character's official rendering style at full-body scale,
which is what a generator needs to match. Class C pins face and costume detail.
Per-class caps keep any one character from dominating the library.

Usage:
    python3 collect_gallery.py --roster ../research/roster-genshin.json --library … --limit 3
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "harness-ui-collector/1.0 (personal, non-commercial)"}

# Class D wins over everything: if a filename matches noise it is dropped even
# when it also looks like art ("Ganyu Icon", "… Wallpaper Icon.png").
NOISE = re.compile(
    r"(icon|emoji|sticker.?pack|item |ui |achievement|element |weapon |artifact|"
    r"namecard.?icon|\.mp4$|\.ogg$|\.webm$|- genshin impact$|- honkai|- zenless|"
    r"logo|button|banner.?ad|qr.?code)", re.I)
STYLE = re.compile(r"(wallpaper|artwork|key.?visual|promotional|teaser|illustration|"
                   r"birthday|anniversary|splash|poster)", re.I)
DETAIL = re.compile(r"(constellation|skill|talent|burst|namecard|portrait|"
                    r"sticker|expression|chibi|sprite)", re.I)

CAPS = {"style": 10, "detail": 8}
API_LIMIT = 500


def api(wiki: str, params: dict, *, timeout: int = 30) -> dict:
    url = f"https://{wiki}.fandom.com/api.php?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as response:
        return json.load(response)


def gallery_files(wiki: str, page: str) -> list[str]:
    """Image titles on a character page and its /Gallery subpage."""
    names: list[str] = []
    for title in (page, f"{page}/Gallery"):
        try:
            data = api(wiki, {"action": "query", "titles": title, "prop": "images",
                              "imlimit": API_LIMIT, "format": "json"})
        except Exception:
            continue
        for entry in data.get("query", {}).get("pages", {}).values():
            if "missing" in entry:
                continue
            names += [image["title"][5:] for image in entry.get("images", [])]
    return sorted(set(names))


def classify(name: str) -> str | None:
    """Class B/C label for a filename, or None to skip."""
    if NOISE.search(name) or not name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        return None
    if STYLE.search(name):
        return "style"
    if DETAIL.search(name):
        return "detail"
    return None


def image_urls(wiki: str, names: list[str]) -> dict[str, str]:
    """Direct file URLs for image titles, 50 per call."""
    out: dict[str, str] = {}
    for start in range(0, len(names), 50):
        chunk = [f"File:{n}" for n in names[start:start + 50]]
        try:
            data = api(wiki, {"action": "query", "titles": "|".join(chunk),
                              "prop": "imageinfo", "iiprop": "url", "format": "json"})
        except Exception:
            continue
        for page in data.get("query", {}).get("pages", {}).values():
            info = (page.get("imageinfo") or [{}])[0]
            if info.get("url"):
                out[page["title"][5:]] = info["url"]
        time.sleep(0.25)
    return out


def slug(text: str) -> str:
    stem = text.rsplit(".", 1)[0]
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", stem.lower())).strip("-")[:70]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--pause", type=float, default=0.25)
    args = parser.parse_args()

    roster = json.loads(args.roster.read_text(encoding="utf-8"))
    wiki, game_zh = roster["wiki"], roster["game_zh"]
    characters = roster["characters"][: args.limit] if args.limit else roster["characters"]

    grand = {"style": 0, "detail": 0}
    for index, character in enumerate(characters, 1):
        if character.get("refs_status") not in ("ok", "cached"):
            continue
        home = args.library / game_zh / character["id"] / "refs"
        ledger_path = home / "gallery.json"
        if ledger_path.exists():
            print(f"  = [{index:>3}/{len(characters)}] {character['name_en']}")
            continue

        names = gallery_files(wiki, character["wiki_page"])
        # Version wallpapers ("Version Luna I Wallpaper 1.png") sit on every
        # character's gallery and often do not show that character at all, so
        # files carrying the character's own name are taken first and the
        # shared ones only fill any remaining slots.
        own = character["name_en"].lower().split()[0]
        picked: dict[str, list[str]] = {"style": [], "detail": []}
        for pass_own in (True, False):
            for name in names:
                label = classify(name)
                if label is None or len(picked[label]) >= CAPS[label]:
                    continue
                if (own in name.lower()) is not pass_own:
                    continue
                if name not in picked[label]:
                    picked[label].append(name)

        urls = image_urls(wiki, picked["style"] + picked["detail"])
        ledger = []
        for label in ("style", "detail"):
            target_dir = home / label
            for name in picked[label]:
                url = urls.get(name)
                if not url:
                    continue
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / f"{slug(name)}.{url.rsplit('.', 1)[-1].split('?')[0][:4]}"
                if not target.exists():
                    try:
                        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as response:
                            target.write_bytes(response.read())
                    except Exception:
                        continue
                    time.sleep(args.pause)
                ledger.append({"class": label, "title": name, "file": f"{label}/{target.name}",
                               "url": url, "bytes": target.stat().st_size})
                grand[label] += 1

        home.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps({
            "character": character["id"], "name_en": character["name_en"],
            "game": roster["game"], "scanned": len(names),
            "counts": {k: sum(1 for e in ledger if e["class"] == k) for k in CAPS},
            "fetched": "2026-08-19",
            "usage": "个人非商业：仅作生成锚定与质量校验，不进入分发产物",
            "rights": "角色与官方美术版权归 miHoYo / HoYoverse",
            "items": ledger,
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        counts = ledger_path and json.loads(ledger_path.read_text())["counts"]
        print(f"  + [{index:>3}/{len(characters)}] {character['name_en']:<22} "
              f"扫 {len(names):>3} 张 → 风格 {counts['style']} · 细节 {counts['detail']}")

    print(f"\n入库：风格参考 {grand['style']} · 细节参考 {grand['detail']}")


if __name__ == "__main__":
    main()
