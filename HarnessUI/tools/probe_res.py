#!/usr/bin/env python3
"""Find each character's best native-resolution anchor on the wiki.

Produces `best-<game>.json`, which `collect_hires.py` consumes.

Two rules decided this file, both learned the expensive way:

*   **Provenance beats resolution.** Picking by pixel area alone grabs the
    gacha banner: 51 of 164 characters got one, Ganyu included — her banner is
    larger than her own splash art. So candidates are filtered by filename
    class FIRST, and only then compared by size. `"<name> Wish.png"` is the
    banner (2048x1024, wide) and is excluded outright.
*   **Portrait beats area.** A wide banner has more pixels but the character
    is cropped, so an upright candidate always wins over a landscape one.

Usage:
    python3 probe_res.py --game wuwa --roster ../research/roster-wuwa.json \
        --out ../../scratchpad/best-wuwa.json
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
WIKIS = {"genshin": "genshin-impact", "hsr": "honkai-star-rail",
         "zzz": "zenless-zone-zero", "wuwa": "wutheringwaves"}
CANDIDATES = {
    "genshin": ["{n} Card.png", "Character {n} Full Wish.png",
                "Character {n} Full Wish Alt.png", "Character {n} Portrait.png"],
    "hsr": ["Character {n} Splash Art.png", "Character {n} Card.png",
            "{n} Card.png", "Character {n} Portrait.png", "Character {n} Full.png"],
    "zzz": ["Agent {n} Full.png", "Mindscape {n} Partial.png",
            "Agent {n} Portrait.png", "{n} Card.png", "Agent {n} Splash Art.png"],
    "wuwa": ["{n} Full Sprite.png", "{n} Splash Art.png", "{n} Card.png",
             "{n} Portrait.png"],
}


def api(wiki: str, params: dict, *, timeout: int = 30) -> dict:
    url = f"https://{wiki}.fandom.com/api.php?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return json.load(r)
    except Exception:
        return {}


def image_info(wiki: str, titles: list[str]) -> dict:
    """width/height/url for a batch of File: titles."""
    found = {}
    for i in range(0, len(titles), 40):
        data = api(wiki, {"action": "query", "titles": "|".join(titles[i:i + 40]),
                          "prop": "imageinfo", "iiprop": "url|size", "format": "json"})
        for page in data.get("query", {}).get("pages", {}).values():
            info = (page.get("imageinfo") or [None])[0]
            if info and info.get("width"):
                found[page["title"]] = (info["width"], info["height"], info["url"])
        time.sleep(0.2)
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True, choices=WIKIS)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    wiki = WIKIS[args.game]
    roster = json.loads(args.roster.read_text(encoding="utf-8"))
    best: dict = {}
    upright = landscape = none = 0

    for character in roster["characters"]:
        page = (character.get("wiki_page") or character["id"]).replace("_", " ").split("/")[0]
        titles = [f"File:{p.format(n=page)}" for p in CANDIDATES[args.game]]
        found = image_info(wiki, titles)
        if not found:
            best[character["id"]] = None
            none += 1
            print(f"  - {character['id']:<22} 无候选")
            continue
        # 竖构图优先，其次面积：横幅像素多但人物是被裁过的
        title, (w, h, url) = max(found.items(),
                                 key=lambda kv: (1 if kv[1][1] >= kv[1][0] else 0,
                                                 kv[1][0] * kv[1][1]))
        best[character["id"]] = {"title": title, "url": url, "w": w, "h": h}
        if h >= w:
            upright += 1
        else:
            landscape += 1
        print(f"  + {character['id']:<22} {w}x{h}  {title[5:]}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(best, ensure_ascii=False, indent=2), encoding="utf-8")
    sizes = sorted(min(v["w"], v["h"]) for v in best.values() if v)
    median = sizes[len(sizes) // 2] if sizes else 0
    print(f"\n竖 {upright} · 横 {landscape} · 无候选 {none} · 短边中位数 {median}px")
    print(f"→ {args.out}")


if __name__ == "__main__":
    main()
