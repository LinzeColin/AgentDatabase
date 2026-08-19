#!/usr/bin/env python3
"""Upgrade each character's anchor from the card art to the full splash art.

`collect_refs.py` takes whatever the wiki nominates as the page image, which is
the small character *card* — a cropped bust on a plain plate. The full-body
splash art exists on the same wikis under a predictable name and carries far
more of what an anchor has to carry: the whole silhouette, the full costume,
the accessories, the pose.

Since identity in this pipeline comes entirely from the anchor and not from the
prompt, anchor resolution is the single biggest lever on whether a generated
character is recognisable. Card art was leaving most of that on the table.

Naming differs per wiki (verified 2026-08-19):

    genshin  Character <Name> Full Wish.png
    hsr      Character <Name> Splash Art.png
    zzz      Mindscape <Name> Partial.png   /  Agent <Name> Full.png

Writes `refs/splash.png` and records it in `source.json`; the card stays as
`portrait.png` so nothing that already points at it breaks.

Usage:
    python3 collect_splash.py --roster ../research/roster-genshin.json --library …
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

# Ordered candidates per game: the first that resolves wins.
PATTERNS = {
    "genshin": ["Character {name} Full Wish.png", "Character {name} Full Wish Alt.png"],
    "hsr": ["Character {name} Splash Art.png", "Character {name} Splash.png"],
    "zzz": ["Mindscape {name} Partial.png", "Agent {name} Full.png",
            "Mindscape {name} Full.png"],
}


def api(wiki: str, params: dict, *, timeout: int = 25) -> dict:
    url = f"https://{wiki}.fandom.com/api.php?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as response:
        return json.load(response)


def find_splash(wiki: str, game: str, page: str, display: str) -> tuple[str, str] | None:
    """(file title, url) of the best splash art for one character.

    Tries the naming templates first, then falls back to scanning the character
    page's own image list — new characters occasionally land with a variant
    spelling before an editor normalises it.
    """
    names = [pattern.format(name=display) for pattern in PATTERNS[game]]
    names += [pattern.format(name=page.replace("_", " ")) for pattern in PATTERNS[game]]

    for name in dict.fromkeys(names):
        try:
            data = api(wiki, {"action": "query", "titles": f"File:{name}",
                              "prop": "imageinfo", "iiprop": "url", "format": "json"})
        except Exception:
            continue
        for entry in data.get("query", {}).get("pages", {}).values():
            info = (entry.get("imageinfo") or [{}])[0]
            if info.get("url"):
                return name, info["url"]

    try:
        data = api(wiki, {"action": "query", "titles": page, "prop": "images",
                          "imlimit": 500, "format": "json"})
    except Exception:
        return None
    probe = re.compile(r"(full wish|splash art|mindscape.*partial|agent .*full)", re.I)
    for entry in data.get("query", {}).get("pages", {}).values():
        for image in entry.get("images", []):
            title = image["title"][5:]
            if probe.search(title) and not re.search(r"icon", title, re.I):
                try:
                    info_data = api(wiki, {"action": "query", "titles": image["title"],
                                           "prop": "imageinfo", "iiprop": "url", "format": "json"})
                except Exception:
                    continue
                for info_page in info_data.get("query", {}).get("pages", {}).values():
                    info = (info_page.get("imageinfo") or [{}])[0]
                    if info.get("url"):
                        return title, info["url"]
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--pause", type=float, default=0.3)
    args = parser.parse_args()

    roster = json.loads(args.roster.read_text(encoding="utf-8"))
    wiki, game, game_zh = roster["wiki"], roster["game"], roster["game_zh"]
    characters = roster["characters"][: args.limit] if args.limit else roster["characters"]

    upgraded = cached = missing = 0
    gaps = []
    for index, character in enumerate(characters, 1):
        refs = args.library / game_zh / character["id"] / "refs"
        if not (refs / "portrait.png").exists():
            continue
        target = refs / "splash.png"
        if target.exists():
            cached += 1
            continue

        found = find_splash(wiki, game, character["wiki_page"], character["name_en"])
        if found is None:
            missing += 1
            gaps.append(character["name_en"])
            print(f"  - [{index:>3}/{len(characters)}] {character['name_en']}")
            continue

        title, url = found
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as response:
                target.write_bytes(response.read())
        except Exception as error:
            missing += 1
            gaps.append(f"{character['name_en']} (下载失败)")
            print(f"  ! [{index:>3}/{len(characters)}] {character['name_en']} {str(error)[:40]}")
            continue

        record = refs / "source.json"
        if record.exists():
            data = json.loads(record.read_text(encoding="utf-8"))
            data.setdefault("files", []).append({
                "file": "splash.png", "kind": "official-splash-art",
                "url": url, "wiki_title": title, "bytes": target.stat().st_size,
            })
            data["anchor"] = "splash.png"   # 生成锚定优先用它
            record.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

        upgraded += 1
        card = (refs / "portrait.png").stat().st_size
        print(f"  + [{index:>3}/{len(characters)}] {character['name_en']:<22} "
              f"{card // 1024}KB → {target.stat().st_size // 1024}KB")
        time.sleep(args.pause)

    print(f"\n升级 {upgraded} · 已有 {cached} · 找不到 {missing}")
    if gaps:
        print("无全身立绘（仍用角色卡做锚图）：" + ", ".join(gaps[:20]))


if __name__ == "__main__":
    main()
