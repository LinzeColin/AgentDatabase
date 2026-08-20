#!/usr/bin/env python3
"""Collect every alternate outfit / skin into the material library.

The base collector (`collect_refs.py`) takes one portrait per character, which
is only the default look. Characters ship alternate outfits — 150 on the
Genshin wiki, 90 on Zenless, 28 on Star Rail — and a skin library that carries
only default looks covers a fraction of what the roster can actually produce.

Each outfit lives on its own wiki page, and two fields there do all the work:
the page image is the outfit's full splash art, and the page's categories
include `<Character> Outfits`, which is how an outfit is attributed back to its
owner without any hand-maintained mapping.

Writes to `<library>/<游戏>/<角色>/refs/outfits/<outfit>.png` alongside a
per-character `outfits.json` ledger.

Usage:
    python3 collect_outfits.py --roster ../research/roster-genshin.json --library …
    python3 collect_outfits.py --roster ../research/roster-zzz.json --library … --limit 5
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

UA = {"User-Agent": "harness-ui-collector/1.0 (personal, non-commercial)"}
# "Ganyu Outfits" → Ganyu. Anchored so "Paid Outfits" / "4-Star Outfits" and the
# other bookkeeping categories on the same page never look like a character.
OWNER_CATEGORY = re.compile(r"^(?!Paid |Free |Bundled |\d)(.+?) Outfits$")
# 鸣潮把稀有度也写成 "<词> Outfits" 分类（Deluxe / Premium / Signature /
# Original），正则会把它们当成角色名。Original 尤其要挡：那是角色的默认装，
# 它的图就是 <Name> Full Sprite.png —— 和默认锚图同一个文件，收进来就是重复变体。
SKIP_OWNERS = {"Character", "Traveler", "Trailblazer", "Rover",
               "Deluxe", "Premium", "Signature", "Original", "Standard"}


def api(wiki: str, params: dict, *, timeout: int = 30) -> dict:
    url = f"https://{wiki}.fandom.com/api.php?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as response:
        return json.load(response)


def list_outfits(wiki: str) -> list[str]:
    """Every page in Category:Outfits, following continuation."""
    titles, cont = [], {}
    while True:
        data = api(wiki, {"action": "query", "list": "categorymembers",
                          "cmtitle": "Category:Outfits", "cmlimit": 500,
                          "format": "json", **cont})
        titles += [m["title"] for m in data.get("query", {}).get("categorymembers", [])]
        if "continue" not in data:
            return [t for t in titles if t != "Outfits"]
        cont = data["continue"]


def describe(wiki: str, titles: list[str]) -> dict[str, dict]:
    """Page image + categories for up to 50 outfit pages per call."""
    out = {}
    for start in range(0, len(titles), 50):
        chunk = titles[start:start + 50]
        data = api(wiki, {"action": "query", "titles": "|".join(chunk),
                          "prop": "pageimages|categories", "piprop": "original",
                          "cllimit": "max", "format": "json"})
        for page in data.get("query", {}).get("pages", {}).values():
            owners = []
            for category in page.get("categories", []):
                match = OWNER_CATEGORY.match(category["title"].replace("Category:", ""))
                if match and match.group(1) not in SKIP_OWNERS:
                    owners.append(match.group(1))
            categories = {c["title"].replace("Category:", "") for c in page.get("categories", [])}
            out[page["title"]] = {
                "image": (page.get("original") or {}).get("source"),
                "owners": [] if "Original Outfits" in categories else owners,
            }
        time.sleep(0.3)
    return out


def portrait_file(wiki: str, titles: list[str]) -> dict[str, tuple[str, int, int]]:
    """`<Outfit> Full Sprite.png` — the outfit's own character portrait.

    The page image is NOT reliably a portrait. On the Wuthering Waves wiki the
    outfit page's nominated image is `<Outfit> Splash Art.png`, which is the
    promo key art for the whole scene: 2048x1667 of room, with the character
    small and reclining somewhere inside it. As an identity anchor that is
    worthless — and one of them (Laurel Nymph) was refused outright by the
    image API's safety system, twice, on both light and dark.

    So ask for the sprite by name first and only fall back to the page image
    when the wiki has none.
    """
    wanted = [f"File:{t} Full Sprite.png" for t in titles]
    found: dict[str, tuple[str, int, int]] = {}
    for start in range(0, len(wanted), 40):
        data = api(wiki, {"action": "query", "titles": "|".join(wanted[start:start + 40]),
                          "prop": "imageinfo", "iiprop": "url|size", "format": "json"})
        for page in data.get("query", {}).get("pages", {}).values():
            info = (page.get("imageinfo") or [None])[0]
            if info and info.get("width"):
                outfit = page["title"][5:-len(" Full Sprite.png")]
                found[outfit] = (info["url"], info["width"], info["height"])
        time.sleep(0.25)
    return found


def original_url(url: str) -> str:
    """Fandom 的 CDN 对所有 UA 都返回 WebP 转码；不加这个参数拿到的不是原图。"""
    parts = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qs(parts.query)
    query["format"] = ["original"]
    return urllib.parse.urlunsplit(
        parts._replace(query=urllib.parse.urlencode(query, doseq=True)))


def slug(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--pause", type=float, default=0.3)
    args = parser.parse_args()

    roster = json.loads(args.roster.read_text(encoding="utf-8"))
    wiki, game_zh = roster["wiki"], roster["game_zh"]
    # Match on both the roster short name and the wiki title collect_refs.py
    # resolved and wrote back: outfit categories use the agent's full name
    # ("Evelyn Chevalier", "Hoshimi Miyabi") while the roster carries the short
    # one, which orphaned most Zenless outfits on the first run.
    by_name = {}
    for character in roster["characters"]:
        by_name[character["name_en"]] = character
        page = (character.get("wiki_page") or "").replace("_", " ")
        if page:
            by_name.setdefault(page, character)

    titles = list_outfits(wiki)
    if args.limit:
        titles = titles[: args.limit]
    print(f"{game_zh}: Category:Outfits 共 {len(titles)} 套")

    pages = describe(wiki, titles)
    sprites = portrait_file(wiki, titles)
    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    orphans = []
    for title, info in pages.items():
        sprite = sprites.get(title)
        image = sprite[0] if sprite else info["image"]
        if not image:
            orphans.append(f"{title} (无立绘)")
            continue
        # 场景宣传图当不了身份锚图：人物在里面只占很小一块，
        # 而锚图是这条产线里角色还原度的唯一来源。
        if not sprite:
            orphans.append(f"{title} (只有场景宣传图，没有 Full Sprite)")
            continue
        owner = next((o for o in info["owners"] if o in by_name), None)
        if owner is None:
            orphans.append(f"{title} (归属 {info['owners'] or '未知'} 不在女角色名单)")
            continue
        grouped[owner].append((title, image))

    saved = 0
    for owner, items in sorted(grouped.items()):
        character = by_name[owner]
        home = args.library / game_zh / character["id"] / "refs" / "outfits"
        home.mkdir(parents=True, exist_ok=True)
        ledger = []
        for title, url in items:
            target = home / f"{slug(title)}.png"
            if not target.exists():
                try:
                    with urllib.request.urlopen(urllib.request.Request(original_url(url), headers=UA), timeout=60) as response:
                        target.write_bytes(response.read())
                except Exception as error:
                    orphans.append(f"{title} (下载失败 {str(error)[:40]})")
                    continue
                time.sleep(args.pause)
            ledger.append({"outfit": title, "file": target.name,
                           "url": url, "bytes": target.stat().st_size})
            saved += 1
        (home.parent / "outfits.json").write_text(json.dumps({
            "character": character["id"], "name_en": owner, "game": roster["game"],
            "count": len(ledger), "fetched": "2026-08-19",
            "usage": "个人非商业：仅作生成锚定与质量校验，不进入分发产物",
            "rights": "角色与官方美术版权归 miHoYo / HoYoverse",
            "outfits": ledger,
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"  + {owner:<22} {len(ledger)} 套")

    print(f"\n入库 {saved} 套，覆盖 {len(grouped)} 个角色")
    if orphans:
        print(f"未归入 {len(orphans)} 项（多为男性角色或联动款）：")
        for entry in orphans[:12]:
            print(f"  · {entry}")
        if len(orphans) > 12:
            print(f"  … 还有 {len(orphans) - 12}")


if __name__ == "__main__":
    main()
